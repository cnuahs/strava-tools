# strava-tools

A collection of simple command line tools for manipulating data on [Strava](http://strava.com/).

The tools make use of the [stravalib](https://github.com/hozn/stravalib.git/) and [Flask](http://flask.pocoo.org/) Python modules:

To setup your environment:

```bash
$ git clone https://github.com/hozn/stravalib.git
$ python -m virtualenv --no-site-packages --distribute env
$ source env/bin/activate
(env) $ cd ./stravalib
(env) $ python setup.py develop
(env) $ pip install flask
(env) $ pip install geographiclib
```

You also need to create/register and authorize a Strava App to use the Strava API. To do so:

1. Login to your Strava account.
2. Point your browser at, https://www.strava.com/settings/api.
3. Complete the required fields (Name, Website and Authorization Callback Domain) to register an app. The form is geared towards developers deploying web apps. We're not doing that. In the "Website" field, you can enter any web site you like (I use 'https://www.strava.com/'), and
in the "Authorization Callback Domain", enter 'localhost'.
4. Upload an icon image (this can be anything you like and will appear next to your "app" in the list of authorized apps for your Strava profile).
5. Once your app is registered, take note of the "Client ID", "Client Secret" and "Access Token" that are generated.

Before you can use the command line tools you need to cache the credentials obtained above. To do so, create a file called config.py containing the following:

```python
CLIENT_ID = <your client_id>;
CLIENT_SECRET = <your client_secret>;

users = {
  <name>: <your access_token>
};
```

You're now all set with read access to your profile and activities on Strava.

To obtain an access token with write permissions, call strava-tools.py as follows:

```bash
(env) $ ./strava-tools.py auth [--port <port>]
```

This will open a browser window for you to enter your credentials at Strava.com, and will retrieve your access token. You need to add this token (copy and paste it from your browser) to config.py either in place of or in addition to the read only token you added above.

If you need to navigate a firewall or proxy, you can specify the local port to listen on using the --port option.

You can perform operation of your strava activities using strava-tools.py as follows:

```bash
(env) $ ./strava-tools.py action [--user <name>]
```

where action is the action to perform and the optional argument <name> is a key from the Python dictionary 'users' defined in config.py.

For help, including a list of available actions, type:

```bash
(env) $ ./strava-tools.py -h
```

For action specific help, type:

```bash
(env) $ ./strava-tools.py action -h
```
