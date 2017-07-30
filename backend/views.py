# Flask backend for strava-tools

# 2017-07-30 - Shaun L. Cloherty <s.cloherty@ieee.org>

from flask import request, render_template;

from backend import app, client;

import config; # contains authorized access tokens for the strava api

@app.route('/')
@app.route('/index')
def index():
  return "Welcome to the strava-tools backend."

@app.route('/auth')
def auth_callback():
    code = request.args.get('code'); # extract the code from the auth url
    # logging.info('code = %s', code);
    access_token = client.exchange_code_for_token(
        client_id = config.CLIENT_ID,
        client_secret = config.CLIENT_SECRET,
        code = code);
    # TODO: cache the access token...?
    return render_template('auth.html',token = access_token); # display it in the browser
