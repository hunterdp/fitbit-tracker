# -*- coding: utf-8 -*-
"""Simple retrieving of fitbit information.

A simple module to collect fitbit information, parse it and either
store, graph, chart or simply display the data.

The basic flow of the program is:
	- Parse options
	- Read in configuration file and retrieve an OUTH2 token
	- Process the requested options
Attributes:

Todo:

"""
# Imports
import argparse
import json
import os.path
import sys
import requests

# import specific packages
from os import path
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import MobileApplicationClient

# Globals

# Process arguments
usage = 'Retrieves various information from the Fitbit website.'
parser = argparse.ArgumentParser(description=usage)
parser.add_argument("config", help="Name of the configuration file")
parser.add_argument("-d", "--debug", help="debug messages on", action="store_true")


# Process command line arguments
args = parser.parse_args()

if args.config:
  if path.exists(args.config):
    if args.debug:
      print "Setting config file to {}", args.config
    config_file=args.config
  else:
    print("Configuration file does not exist.")
    exit(0)

if args.debug: print ("The Python version we are running on is: ", sys.version_info)

with open(config_file) as json_config_file:
  data = json.load(json_config_file)

scope = data['auth_scopes']
client_id = data['client_id']
client_secret = data['client_secret']
token_expiration = data['token_expires']
fitbit_base_url = data['base_url']
fitbit_api_base_url = data['api_url']
fitbit_auth2_url = data['auth2_url']
app_redirect_url = data['redirect_url']

if args.debug:
  print(data['auth_scopes'])
  print(data['client_id'])
  print(data['base_url'])
  print(data['redirect_url'])
  print(data['client_secret'])
  print(data['token_expires'])
  print(data['api_url'])

if args.debug: print(json.dumps(data, indent=2))

# Initialize the client
client = MobileApplicationClient(client_id)
fitbit = OAuth2Session(client_id, client=client, scope=scope)

# Authorize the client
auth_url, state = fitbit.authorization_url(fitbit_auth2_url)
print 'auth2_url = ', auth_url
res = requests.get(auth_url, allow_redirects=False)
print 'res response is:', res.status_code
print 'res.text = \n', res.text
print 'res.history = ',res.history
print 'res.headers[Location] = ', res.headers['Location']

