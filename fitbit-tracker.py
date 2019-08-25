# -*- coding: utf-8 -*-
"""Simple retrieving of fitbit information.

A simple module to collect fitbit information, parse it and store it in csv files. 
The configuration infomration is read from the .json file passed in and must be submitted.
There are various command line options that allow the collectin of a specified day in 
relation to the current day.  By default the program will collect data from yesterday
and store it accordinly.

To collect data over long periods of time, put this into a script and call it once a
day.  This will generate a directory of data files suitable for post processing.

"""
# Imports
import fitbit
import argparse
import json
import os.path
import sys
import requests
import pandas as pandas

from os import path
from datetime import datetime 
from datetime import timedelta

# Globals
AUTHOR = 'David Hunter'
VERSION = 'fitbit-tracker ver 0.02'

# Setup the valid arguments and then process.  Note we must have a configuration file.
usage = 'Retrieves various information from the Fitbit website.'
parser = argparse.ArgumentParser(prog='Fitbit Tracker', description=usage)

# Add the arguments
parser.add_argument('config', help='Name of the configuration file', type=str)
parser.add_argument('-a', '--all', help='collect all the data possible', action='store_true')
parser.add_argument('--days', help='number of days to go back', 
                    action='store', type=int, dest='number_of_days', default='1')
parser.add_argument('-d', '--debug', help='turn on debug messages', action='store_true', default=False)
parser.add_argument('-o', '--output',  help='output directory to store results files', 
                    action='store', type=str,  dest='output_dir', default='results')                    
parser.add_argument('-t', '--type', help='collect only the type of data specified (heartrate, sleep, steps)',
                    action='store', type=str, dest='collect_type')
parser.add_argument('-v', '--version', help='prints the version', action='version', version=VERSION)

args = parser.parse_args()

# Make sure all options are valid
if args.config:
  if path.exists(args.config):
    config_file=args.config
  else:
    print("Configuration file does not exist.")
    exit(0)

if not args.number_of_days:
  number_of_days = 1
elif args.number_of_days < 0:
  print("Number of days needs to be greater than zero")
  exit(0)
else:
  number_of_days = args.number_of_days

if not os.path.isdir(args.output_dir):
  print('Directory does not exist')
  exit(0)
else:
  output_dir = args.output_dir

# define a few common dates
today = datetime.today()
yesterday = today - timedelta(days=number_of_days)
yesterday_str = datetime.strftime(yesterday,"%Y-%m-%d")

# Create the result file names
heartrate_file = output_dir + '\\' + 'hr_intraday_' + yesterday_str + '.csv'
steps_file = output_dir + '\\' + 'steps_intraday_' + yesterday_str + '.csv'
sleep_file = output_dir + '\\' + 'sleep_day_' + yesterday_str + '.csv'

# Open and read in the configuration information.  Note that the file must contain the following fields:
#    "base_url":"https://www.fitbit.com/"
#    "api_url":"https://api.fitbit.com"
#    "auth2_url":"https://fitbit.com/oauth2/authorize"
#    "client_id":"<clien_id from fitbit website>"
#    "client_secret":"<client secret from fitbit web site"
#    "redirect_url":"<uri redirect from fitbit website>"
#    "auth_scopes":"activity, profile, weight, heatrate, settings, sleep"
#    "token_expires":"<see note below>"
#    "access_token": "<see the note below>"
#    "refresh_token": "<seenote below>"
# Note:
#   To make it easier, use the OAuth 2.0 tutorial page (https://dev.fitbit.com/apps/oauthinteractivetutorial) to get these

with open(config_file) as json_config_file:
  data = json.load(json_config_file)
  if args.debug: print(json.dumps(data, indent=2, sort_keys=True))

# See the page https://dev.fitbit.com/build/reference/web-api/oauth2/
if data['access_token'] == '':
  print("No access token found.  Please generate and place in the configuration file.")
  exit(0)

# Create an oauth and oauth2 client (we mostly use the oauth2 client)
authd_client = fitbit.Fitbit(data['client_id'], data['client_secret'], access_token=data['access_token'])
authd_client2 = fitbit.Fitbit(data['client_id'], data['client_secret'], oauth2=True, access_token=data['access_token'], refresh_token=data['refresh_token'])

# Retrieve the interval heart rate data and store in a panda data frame.  We grab the highest
# fidelity we can which is at best 1 second.  Note that it may not be exactly 1 second.  We will basically be 
# one day behind today, so we start at midnight yesterday and go to 23:59 yesterday
hr_intraday = authd_client2.intraday_time_series('activities/heart', base_date=yesterday, start_time='00:00', end_time='23:59', detail_level='1sec')
time_list = []
value_list = []
for i in hr_intraday['activities-heart-intraday']['dataset']:
  value_list.append(i['value'])
  time_list.append(i['time'])
heartrate_df = pandas.DataFrame({'Time':time_list,'Heart Rate':value_list})

# retrieve steps series and store in a panda data frame.  We will use a fidelity of 15 minutes.
steps_intraday = authd_client2.intraday_time_series('activities/steps', base_date=yesterday, start_time='00:00', end_time='23:59', detail_level='15min')
time_list = []
value_list = []
for i in steps_intraday['activities-steps-intraday']['dataset']:
  value_list.append(i['value'])
  time_list.append(i['time'])
steps_df = pandas.DataFrame({'Time':time_list,'Steps':value_list})

# Retrieve the sleep data.  We need to translate the "value" if sleep into the different categories so
# it can be aligned with the heartbeat data.  Maping for the values are: 1-asleep, 2-restless, 3-awake
single_day_sleep = authd_client2.get_sleep(yesterday)
time_list = []
value_list = []
for i in single_day_sleep['sleep'][0]['minuteData']:
  value_list.append(i['value'])
  time_list.append(i['dateTime'])
sleep_df = pandas.DataFrame({'Time':time_list,'Sleep Type':value_list})

# print out simple stats of the collections
# TODO(dph): We should save this data somewhere although it is easily reproducable when the dataset is read back in
print(heartrate_df.describe())
print(steps_df.describe())
print(sleep_df.describe())

# Save the data into a local files.  We want to save the data on a per-day basis so use the naming convention YY-MM-DD.csv
heartrate_df.to_csv(heartrate_file, columns=['Time','Heart Rate'], header=True, index=False)
steps_df.to_csv(steps_file, columns=['Time','Steps'], header=True, index=False)
sleep_df.to_csv(sleep_file, columns=['Time','Sleep Type'], header=True, index=False)


