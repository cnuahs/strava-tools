#!/usr/bin/env python
'''
Command line tool(s) for Strava.
'''

# 2017-07-29 - Shaun L. Cloherty <s.cloherty@ieee.org>

import os, getpass, sys, time, random, webbrowser;

from datetime import datetime;

from argparse import ArgumentParser;
import argparse;

from backend import client, app; # strava-tools backend

import logging;

def auth(client_id,client_secret,port):
    # perform Strava OAuth authorization...
    #
    # note: passing the client_id and client_secret in the url
    #       isn't recommended!
    url = client.authorization_url(
            client_id = client_id,
            # redirect_uri = 'http://localhost:{0}/auth?client_id={1}&client_secret={2}'.format(port,client_id,client_secret), # nasty hack, bad idea!
            redirect_uri = 'http://localhost:{0}/auth'.format(port),
            scope = ['read_all','activity:write']);

    # open url in the default browser
    webbrowser.open_new_tab(url);

    # launch the flask backend to catch the OAuth redirect from strava.com
    app.run(port = port);


def gearCmd(client,args):
    # tag activities with specified gearId

    id = getattr(args,'gearId');
    if id is None:
        # list all bikes
        athlete = client.get_athlete();
        for id in athlete.bikes:
            logging.info("Bike: %s (%s) %ikm",id.name,id.id,id.distance/1e3);
        return

    cnt = [0,0];
    for activity in client.get_activities(after = getattr(args,'after'),
        before = getattr(args,'before')):
        if activity.gear_id is None:
            if not getattr(args,'dryrun'):
                client.update_activity(activity_id = activity.id,gear_id = id);
                dt = random.expovariate(1.0/1.5); # rate limiting...
                logging.info("Sleeping %fs", dt);
                time.sleep(dt);
            cnt[1] += 1;

        cnt[0] += 1;

    logging.info("Total activities: %i, Updated activities: %i.",cnt[0],cnt[1]);

    return 0;


def commuteCmd(client,args):
    # tag activities as commutes

    # for our purposes, we define a commute as a sequence of rides starting at
    # orig (e.g., home) and ending at dest (e.g., work)

    import config; # see config.py

    orig = getattr(args,'orig');
    if orig is None:
        try:
            orig = config.orig[getattr(args,'user')]
        except AttributeError:
            raise;

    dest = getattr(args,'dest');
    if dest is None:
        try:
            dest = config.dest[getattr(args,'user')]
        except AttributeError:
            raise;

    tol = getattr(args,'tol');
    if tol is None:
        try:
            tol = config.tol;
        except AttributeError:
            tol = 1e3; # default: 1km

    ride = []; # empty list

    # loop over activities, getting id, date, start and end coords
    for activity in client.get_activities(after = getattr(args,'after'),
        before = getattr(args,'before')):
        info = {"id": None, "date": None, "start": None, "end": None}; info["id"] = activity.id;
        info["date"] = activity.start_date_local;
        info["name"] = activity.name;
        info["distance"] = activity.distance;
        for latlng in [orig, dest]:
            if distance(latlng,activity.start_latlng) <= tol:
                info["start"] = latlng;
            if distance(latlng,activity.end_latlng) <= tol:
                info["end"] = latlng;
        ride.append(info);

    commute = getCommutes(ride,orig,dest);
    if args.rtrn:
        commute.extend(getCommutes(ride,dest,orig));

    # also flag dest-dest rides as commutes...?
    # TODO: this is a hack, fix this (shaun)
    for r in ride:
        if r["start"] == dest and r["end"] == dest:
            commute.append(r);

    # commute.sort(key = lambda x: x["date"]);

    logging.debug("Found %i/%i activities that look like commutes...",
        len(commute),len(ride));

    for activity in commute:
        logging.debug("{0}: {1} {2} [{3}]".format(activity["date"],activity["name"],activity["distance"],activity["id"]));
        if not getattr(args,'dryrun'):
            client.update_activity(activity_id = activity["id"],commute = True);
            dt = random.expovariate(1.0/1.5); # rate limiting...
            logging.info("Sleeping %fs", dt);
            time.sleep(dt);

    logging.info("Total activities: %i, Updated activities: %i.",
        len(ride),len(commute));


def getCommutes(ride,latlng0,latlng1):
    # sort by date/time... newest to oldest
    ride.sort(key = lambda x: x["date"], reverse = True);

    commute = []; # empty list
    for ii in range(len(ride)):
        # print "{0}: {1}".format(ii,ride[ii]);
        if ride[ii]["start"] != latlng0:
            continue

        # a candidate commute
        if ride[ii]["end"] == latlng0:
            continue # not a commute...
        if ride[ii]["end"] == latlng1:
            commute.append(ride[ii]);
            continue

        # ride could be part of a "multi-ride" commute
        commute_ = [ride[ii]];
        jj = 1;
        while True:
            if ride[ii-jj]["date"].date() != ride[ii]["date"].date():
                # not a commute
                # TODO: could be multi-day commute?
                commute_ = [];
                break
            if ride[ii-jj]["start"] == latlng0 or ride[ii-jj]["end"] == latlng0:
                # not a commute
                commute_ = [];
                break
            if ride[ii-jj]["end"] == latlng1:
                commute_.extend(ride[ii-jj:ii]);
                break
            jj += 1;

        commute.extend(commute_);

    return commute;


def main(args):
    logging.basicConfig(stream = sys.stderr,
                        format='%(levelname)s:%(message)s',
                        level = args.loglevel or logging.INFO);

    logging.debug("args = %s", args);

    import config; # see config.py

    if getattr(args,'action') == "auth":
        # perform OAuth authorization...
        auth(config.CLIENT_ID,config.CLIENT_SECRET,port = getattr(args,'port'))
        return

    try:
        client.access_token = config.users[getattr(args,'user')];
    except KeyError:
        logging.error("Unknown user %s!", getattr(args,'user'));
        return;

    # parse filter arguments...
    before = getattr(args,'before')
    if before is not None:
        try:
            args.before = datetime.strptime(before,'%Y-%m-%d')
        except ValueError:
            logging.error("Invalid date format %s.",before);
            return

    after = getattr(args,'after')
    if after is not None:
        try:
            args.after = datetime.strptime(after,'%Y-%m-%d')
        except ValueError:
            logging.error("Invalid date format %s.",after);
            return

    # this is where we break out to handle different actions...
    return args.cmdfn(client,args);


# compute geodesic distance (in meters) from p0 to p1
def distance(latlng0,latlng1):
    from geographiclib.geodesic import Geodesic;
    geod = Geodesic.WGS84 # use the WGS84 ellipsoid??

    g = geod.Inverse(latlng0[0], latlng0[1], latlng1[0], latlng1[1])
    return g['s12'] # distance in meters


if __name__ == "__main__":
    prog = os.path.basename(sys.argv[0]);

    rev = 0.2; # increment this if modifying the script

    version = "%s v%s" % (prog, rev);

    p = ArgumentParser(
            description = __doc__,
            conflict_handler = "resolve");

    # common options/arguments
    pcommon = ArgumentParser(add_help = False);

    pcommon.add_argument("--version", action = "version", version = version);

    # control debugging output/verbosity
    group = pcommon.add_mutually_exclusive_group();
    group.add_argument("-v","--verbose",
            action = "store_const", const = logging.DEBUG,
            dest = "loglevel",
            help = "increase verbosity");
    group.add_argument("-q","--quiet",
            action = "store_const", const = logging.WARN,
            dest = "loglevel",
            help = "suppress non-error messages");

    # optional arguments
    pcommon.add_argument("-u","--user",
            action = 'store',
            default = getpass.getuser(),
            help = "Strava user/token defined in config.py");

    pcommon.add_argument("-n","--dry-run",
            action = "store_const", const = True,
            default = False,
            dest = "dryrun",
            help = "show what would have been modified");

    pfilter = ArgumentParser(add_help = False);
    pfilter.add_argument("--before",
            action = 'store',
            default = None,
            metavar = "YYYY-MM-DD",
            help = "get activities before date");
    pfilter.add_argument("--after",
            action = 'store',
            default = None,
            metavar = "YYYY-MM-DD",
            help = "get activities after date");
    # pfilter.add_argument("-a","--activity",
    #         action = 'store',
    #         default = None,
    #         metavar = "ID",
    #         help = "activity identifier (e.g., ????????)");

    # actions...
    subparsers = p.add_subparsers(title = "actions",
            dest = "action");

    # auth cmd
    poauth = subparsers.add_parser("auth",
            parents = [pcommon],
            help = "get Strava OAuth access token");
    poauth.add_argument("-p","--port",
            action = 'store',
            default = "8282", # can be anything >1024?
            help = "local port for OAuth callback");

    # gear cmd
    pgear = subparsers.add_parser("gear",
            parents = [pcommon, pfilter],
            help = "add gear to activities");
    pgear.set_defaults(cmdfn = gearCmd)
    pgear.add_argument("-i","--id",
            action = "store",
            default = None,
            dest = "gearId",
            metavar = "ID",
            help = "gear identifier (e.g., b4063944)");

    # commute cmd
    pcommute = subparsers.add_parser("commute",
            parents = [pcommon, pfilter],
            help = "automatically flag commutes");
    pcommute.set_defaults(cmdfn = commuteCmd)
    pcommute.add_argument("-o","--orig",
            action = "store",
            default = None,
            dest = "orig",
            metavar = "(LAT,LNG)",
            help = "origin for your commute");
    pcommute.add_argument("-d","--dest",
            action = "store",
            default = None,
            dest = "dest",
            metavar = "(LAT,LNG)",
            help = "destination for your commute");
    pcommute.add_argument("-t","--tolerance",
            action = "store",
            default = None,
            dest = "tol",
            help = "tolerance for matching orig/dest");
    pcommute.add_argument("-r","--return",
            action = "store_const", const = True,
            default = False,
            dest = "rtrn",
            help = "tag return (dest --> orig) as a commute also");

    args = p.parse_args();
    exit(main(args));
