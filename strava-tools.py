#!/usr/bin/env python
'''
Command line tool(s) for Strava.
'''

# 2017-07-29 - Shaun L. Cloherty <s.cloherty@ieee.org>

import os, sys, time, random, webbrowser;

from argparse import ArgumentParser;
import argparse;

from backend import client, app; # strava-tools backend

import logging;

def auth(client_id,client_secret,port):
    # from backend import app;
    # build auth url
    #
    # note: passing the client_id and client_secret in the url probably
    #       isn't recommended!
    url = client.authorization_url(
            client_id = client_id,
            # redirect_uri = 'http://localhost:{0}/auth?client_id={1}&client_secret={2}'.format(port,client_id,client_secret), # nasty hack, bad idea!
            redirect_uri = 'http://localhost:{0}/auth'.format(port),
            scope = 'view_private,write');
    # open url in the default browser
    webbrowser.open_new_tab(url);

    # launch the flask backend to catch the OAuth redirect from strava.com
    app.run(port = port);


def main(args):
    logging.basicConfig(stream = sys.stderr,
                        format='%(levelname)s:%(message)s',
                        level = args.loglevel or logging.INFO);

    logging.debug("args = %s", args);

    import config; # see config.py

    if getattr(args,'auth'):
        # perform OAuth authorization...
        auth(config.CLIENT_ID,config.CLIENT_SECRET,port = getattr(args,'port'))
        return

    try:
        client.access_token = config.users[getattr(args,'user')];
    except KeyError:
        logging.error("Unknown user %s!", getattr(args,'user'));
        return;

    # FIXME: this is where we'd break out to handle different actions...
    #        for now, just perform the task at hand: set gear_id for any
    #        activity where gear_id is None

    cnt = [0,0];
    for activity in client.get_activities():
        if activity.gear_id is None:
            client.update_activity(activity_id = activity.id,gear_id = 'b4063944');
            dt = random.expovariate(1.0/1.5); # rate limiting...
            logging.info("Sleeping %fs", dt);
            time.sleep(dt);
            cnt[1] += 1;
        # else:
        #     print("{0.id}: {0.name} {0.start_date_local} {0.gear_id} Ok!".format(activity))
        cnt[0] += 1;

    logging.info("Total activities: %i, Updated activities: %i.",cnt[0],cnt[1]);


if __name__ == "__main__":
    prog = os.path.basename(sys.argv[0]);

    rev = 0.1; # increment this if modifying the script

    version = "%s v%s" % (prog, rev);

    p = ArgumentParser(usage = "%(prog)s [options]",
                       description = __doc__,
                       conflict_handler = "resolve");

    # add arguments here
    p.add_argument("--version", action = "version", version = version);

    # control debugging output/verbosity
    group = p.add_mutually_exclusive_group();
    group.add_argument("-v","--verbose",
                    action = "store_const", const = logging.DEBUG,
                    dest = "loglevel",
                    help = "increase verbosity");
    group.add_argument("-q","--quiet",
                    action = "store_const", const = logging.WARN,
                    dest = "loglevel",
                    help = "suppress non-error messages");

    # optional arguments
    p.add_argument("-a","--authorize",
                   action = 'store_const', const = True,
                   default = False,
                   metavar = "auth",
                   dest = "auth",
                   help = "get strava access token");
    p.add_argument("-p","--port",
                   action = 'store',
                   default = "8282", # can be anything >1024?
                   metavar = "port",
                   help = "local port for OAuth callback");

    p.add_argument("-u","--user",
                   action = 'store',
                   default = None,
                   metavar = "user",
                   help = "Strava user/token defined in config.py");

    args = p.parse_args();
    exit(main(args));
