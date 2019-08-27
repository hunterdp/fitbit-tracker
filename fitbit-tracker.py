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
import logging

from os import path
from datetime import datetime 
from datetime import timedelta

# Globals
AUTHOR = 'David Hunter'
VERSION = 'fitbit-tracker ver 0.02'

# Setup the valid arguments and then process.  Note we must have a configuration file.
usage = 'Retrieves various information from the Fitbit website.'
parser = argparse.ArgumentParser(prog='Fitbit Tracker', description=usage, formatter_class=argparse.RawDescriptionHelpFormatter)


# Add the arguments
parser.add_argument('configfile', help='Name of the configuration file. (default: %(default)s)', type=str, default='config.json')
parser.add_argument('-a', '--all', help='collect all the data possible', action='store_true')
parser.add_argument('--days', help='number of days to go back', 
                    action='store', type=int, dest='number_of_days', default='1')
parser.add_argument('-d', '--debug', help='Set the debug level [debug info warn] (default: %(default)s)', action='store', 
                     type=str, default='info')
parser.add_argument('-e', '--end_date',  help='end date to collect data from', 
                    action='store', type=str,  dest='end_date')                    
parser.add_argument('-l', '--log_file', help='Set the logfile name. (default: %(default)s)', action='store', 
                     type=str, default='fitbit-tracker.log')
parser.add_argument('-o', '--output',  help='output directory to store results files. (default: %(default)s)', 
                    action='store', type=str,  dest='output_dir', default='results')                    
parser.add_argument('-s', '--start_date',  help='start date to collect data from (mm-dd-yy)', 
                    action='store', type=str,  dest='start_date')                    
parser.add_argument('-t', '--type', help='collect only the type of data specified (heartrate, sleep, steps)',
                    action='store', type=str, dest='collect_type')
parser.add_argument('-v', '--version', help='prints the version', action='version', version=VERSION)

args = parser.parse_args()

# Configure how we want logging to work.  Note that if both the filename and level are specified, the filename will be ignored.

fmt = "%(asctime)-15s %(message)s"
log_file = args.log_file
if args.debug:
  if 'debug' in args.debug:
    logging.basicConfig(filename=log_file, format=fmt, level=logging.DEBUG)
  if 'warn' in args.debug:
    logging.basicConfig(filename=log_file, format=fmt, level=logging.WARNING)
  elif 'info' in args.debug:
    logging.basicConfig(filename=log_file, format=fmt, level=logging.INFO)
  elif 'error' in args.debug:
    logging.basicConfig(filename=log_file, format=fmt, level=logging.ERROR)
  else:
    logging.basicConfig(filename=log_file, format=fmt, level=logging.ERROR)
    logging.error('Invalid debug level.  Exiting the program.')
    exit(0)
else:
  logging.basicConfig(filename=log_file, format=fmt, level=logging.INFO)
  print('We should not get here')
  
# Make sure all options are valid
if args.config:
  if path.exists(args.configfile):
    config_file=args.configfile
  else:
    logging.error("Configuration file does not exist.  Exiting.")
    exit(0)

if not args.number_of_days:
  number_of_days = 1
elif args.number_of_days < 0:
  logging.error("Number of days needs to be greater than zero")
  exit(0)
else:
  number_of_days = args.number_of_days

if not os.path.isdir(args.output_dir):
  logging.error('Directory does not exist')
  exit(0)
else:
  output_dir = args.output_dir

# Build the list of type of data to collect
collect_type = [] 
if args.collect_type:
  collect_type = args.collect_type
  logging.info('Collecting information for: '+ args.collect_type)
  if 'heartrate' in args.collect_type:
    logging.info('Collecting data for intraday heatrate')
  if 'sleep' in args.collect_type:
    print('Collecting sleep information')
  if 'step' in args.collect_type:
    print('Collecting step information')

# Parse the end and start date arguments.  Make sure that they make sense

# define a few common dates
today = datetime.today()
yesterday = today - timedelta(days=number_of_days)
yesterday_str = datetime.strftime(yesterday,"%Y-%m-%d")

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

# Collect the requested information.  Note that we are limited to 150 requests per day.  If we will exceed that, message back to the caller and exit.
# Save the data into a local files.  We want to save the data on a per-day basis so use the naming convention YY-MM-DD.csv
request_limit = 150

# Retrieve the interval heart rate data and store in a panda data frame.  We grab the highest
# fidelity we can which is at best 1 second.  Note that it may not be exactly 1 second.  We will basically be 
# one day behind today, so we start at midnight yesterday and go to 23:59 yesterday
if 'heartrate' in collect_type or 'all' in collect_type:
  hr_intraday = authd_client2.intraday_time_series('activities/heart', base_date=yesterday, start_time='00:00', end_time='23:59', detail_level='1sec')
  time_list = []
  value_list = []
  for i in hr_intraday['activities-heart-intraday']['dataset']:
    value_list.append(i['value'])
    time_list.append(i['time'])
  heartrate_df = pandas.DataFrame({'Time':time_list,'Heart Rate':value_list})
  heartrate_file = output_dir + '\\' + 'hr_intraday_' + yesterday_str + '.csv'
  heartrate_df.to_csv(heartrate_file, columns=['Time','Heart Rate'], header=True, index=False)
  print(heartrate_df.describe())

# retrieve steps series and store in a panda data frame.  We will use a fidelity of 15 minutes.
if 'steps' in collect_type:
  steps_intraday = authd_client2.intraday_time_series('activities/steps', base_date=yesterday, start_time='00:00', end_time='23:59', detail_level='15min')
  time_list = []
  value_list = []
  for i in steps_intraday['activities-steps-intraday']['dataset']:
    value_list.append(i['value'])
    time_list.append(i['time'])
  steps_df = pandas.DataFrame({'Time':time_list,'Steps':value_list})
  steps_file = output_dir + '\\' + 'steps_intraday_' + yesterday_str + '.csv'
  steps_df.to_csv(steps_file, columns=['Time','Steps'], header=True, index=False)
  print(steps_df.describe())

# Retrieve the sleep data.  We need to translate the "value" if sleep into the different categories so
# it can be aligned with the heartbeat data.  Maping for the values are: 1-asleep, 2-restless, 3-awake
if 'sleep' in collect_type:
  single_day_sleep = authd_client2.get_sleep(yesterday)
  time_list = []
  value_list = []
  for i in single_day_sleep['sleep'][0]['minuteData']:
    value_list.append(i['value'])
    time_list.append(i['dateTime'])
  sleep_df = pandas.DataFrame({'Time':time_list,'Sleep Type':value_list})
  sleep_file = output_dir + '\\' + 'sleep_day_' + yesterday_str + '.csv'
  sleep_df.to_csv(sleep_file, columns=['Time','Sleep Type'], header=True, index=False)
  print(sleep_df.describe())


