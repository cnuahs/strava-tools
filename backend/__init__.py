# backend module for strava-tools

# 2017-07-30 - Shaun L. Cloherty <s.cloherty@ieee.org>

from flask import Flask;
from stravalib import Client;

client = Client();

app = Flask(__name__);

from backend import views; # has to be last!
