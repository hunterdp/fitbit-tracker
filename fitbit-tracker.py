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
VERSION = 'fitbit-tracker ver beta-0.5'

# Functions
def get_heartrate (oauth_client, start_date, time_interval, results_file):
  "Retrieve the intraday heartrate at the specified interval and store in data file and returns the dataframe."
  hr = oauth_client.intraday_time_series('activities/heart', base_date=start_date, start_time='00:00', end_time='23:59', detail_level=time_interval)
  logging.debug(json.dumps(hr, indent=2))
  t_list = []
  v_list = []
  for i in hr['activities-heart-intraday']['dataset']:
    v_list.append(i['value'])
    t_list.append(i['time'])
  df = pandas.DataFrame({'Time':t_list,'Heart Rate':v_list})
  df.to_csv(results_file, columns=['Time','Heart Rate'], header=True, index=False)
  return(df);

def get_steps (oauth_client, start_date, time_interval, results_file):
  "Retrieve the step count for the day at the specified interval and store in datafile."
  hr = oauth_client.intraday_time_series('activities/steps', base_date=start_date, start_time='00:00', end_time='23:59', detail_level=time_interval)
  logging.debug(json.dumps(hr, indent=2))
  t_list = []
  v_list = []
  for i in hr['activities-steps-intraday']['dataset']:
    v_list.append(i['value'])
    t_list.append(i['time'])
  df = pandas.DataFrame({'Time':t_list,'Steps':v_list})
  df.to_csv(results_file, columns=['Time','Steps'], header=True, index=False)
  return(df);

def get_sleep (oauth_client, start_date, results_file):
  "Retrieve the sleep data for the day, store in datafile and return the dataframe."
  # Retrieve the sleep data.  We need to translate the "value" if sleep into the different categories so
  # it can be aligned with the heartbeat data.  Maping for the values are: 1-asleep, 2-restless, 3-awake
  sleep = authd_client2.get_sleep(start_date)
  logging.debug(json.dumps(sleep, indent=2))
  t_list = []
  v_list = []
  for i in sleep['sleep'][0]['minuteData']:
    v_list.append(i['value'])
    t_list.append(i['dateTime'])
  df = pandas.DataFrame({'Time':t_list,'Sleep Type':v_list})
  df.to_csv(results_file, columns=['Time','Sleep Type'], header=True, index=False)
  return(df);

def set_command_options():
  "Sets the command line arguments."
  # Setup the valid arguments and then process.  Note we must have a configuration file.
  usage = 'Retrieves various information from the Fitbit website.'
  parser = argparse.ArgumentParser(prog='Fitbit Tracker', description=usage, formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('configfile', help='Name of the configuration file. (default: %(default)s)', type=str, default='config.json')
  parser.add_argument('-a', '--all', help='collect all the data possible', action='store_true')
  parser.add_argument('--days', help='number of days to go back', action='store', type=int, dest='number_of_days', default='1')
  parser.add_argument('-d', '--debug', help='Set the debug level [debug info warn] (default: %(default)s)', action='store', type=str, default='info')
  parser.add_argument('-e', '--end_date',  help='end date to collect data from', action='store', type=str,  dest='end_date')                    
  parser.add_argument('-l', '--log_file', help='Set the logfile name. (default: %(default)s)', action='store', type=str, default='fitbit-tracker.log')
  parser.add_argument('-o', '--output',  help='output directory to store results files. (default: %(default)s)', action='store', type=str,  dest='output_dir', default='results')                    
  parser.add_argument('-s', '--start_date',  help='start date to collect data from (mm-dd-yy)', action='store', type=str,  dest='start_date')                    
  parser.add_argument('-t', '--type', help='collect only the type of data specified (heartrate, sleep, steps)', action='store', type=str, dest='collect_type')
  parser.add_argument('-v', '--version', help='prints the version', action='version', version=VERSION)
  args = parser.parse_args()
  return(parser);

def get_command_options(parser):
  "Retrieves the command line options and returns a kv dict"
  args = parser.parse_args()
  fmt = "%(asctime)-15s %(message)s"
  log_file = args.log_file
  options = {'log_file' : args.log_file}
  logging.basicConfig(filename=args.log_file, format=fmt, level=logging.INFO)

  if args.debug:
    if 'debug' in args.debug:
      logging.basicConfig(level=logging.DEBUG)
    if 'warn' in args.debug:
      logging.basicConfig(level=logging.WARNING)
    elif 'info' in args.debug:
      logging.basicConfig(level=logging.INFO)
    elif 'error' in args.debug:
      logging.basicConfig(level=logging.ERROR)
    else:
      logging.basicConfig(level=logging.ERROR)
      logging.error('Invalid debug level.  Exiting the program.')
      exit(0)
  
  # Make sure all options are valid
  if args.configfile:
    if path.exists(args.configfile):
      options['config_file'] = args.configfile
    else:
      logging.error("Configuration file does not exist.  Exiting.")
      exit(0)

  if not args.number_of_days:
    options['number_of_days'] = 1
  elif args.number_of_days < 0:
    logging.error("Number of days needs to be greater than zero")
    exit(0)
  else:
    options['number_of_days'] = args.number_of_days

  if not os.path.isdir(args.output_dir):
    logging.error('Directory does not exist')
    exit(0)
  else:
    options['output_dir'] = args.output_dir

  # Build the list of type of data to collect
  if args.collect_type:
    options['collect_type'] = args.collect_type
    logging.info('Collecting information for: '+ args.collect_type)
  
  # Parse the end and start date arguments.  Make sure that they make sense

  return(options)

def get_config():
  "Read in the configuration file and return configuration as a dict"
  configuration = {}
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
  return(configuration);


### MAIN PROGRAM STARTS HERE ###

parser = set_command_options()
options = get_command_options(parser)
print(json.dumps(options))
# define a few common dates
today = datetime.today()
yesterday = today - timedelta(days=options['number_of_days'])
yesterday_str = datetime.strftime(yesterday,"%Y-%m-%d")

with open(options['config_file']) as json_config_file:
  data = json.load(json_config_file)
  
# See the page https://dev.fitbit.com/build/reference/web-api/oauth2/
if data['access_token'] == '':
  print("No access token found.  Please generate and place in the configuration file.")
  logging.error('No access token found.  Exiting.')
  exit(0)
authd_client = fitbit.Fitbit(data['client_id'], data['client_secret'], access_token=data['access_token'])
authd_client2 = fitbit.Fitbit(data['client_id'], data['client_secret'], oauth2=True, access_token=data['access_token'], refresh_token=data['refresh_token'])

# Collect the requested information.  Note that we are limited to 150 requests per day.  If we will exceed that, message back to the caller and exit.
request_limit = 150

if 'heartrate' in options['collect_type'] or 'all' in collect_type:
  heartrate_file = options['output_dir'] + '\\' + 'hr_intraday_' + yesterday_str + '.csv'
  heartrate_df = get_heartrate(oauth_client=authd_client2, start_date=yesterday, time_interval='1sec', results_file=heartrate_file)
  print(heartrate_df.describe())

if 'steps' in options['collect_type'] or 'all' in collect_type:
  steps_file = options['output_dir'] + '\\' + 'steps_intraday_' + yesterday_str + '.csv'
  steps_df = get_heartrate(oauth_client=authd_client2, start_date=yesterday, time_interval='15min', results_file=steps_file)
  print(steps_df.describe())

if 'sleep' in options['collect_type'] or 'all' in collect_type:
  sleep_file = options['output_dir'] + '\\' + 'sleep_day_' + yesterday_str + '.csv'
  sleep_df = get_sleep(oauth_client=authd_client2, start_date=yesterday, results_file=sleep_file)
  print(sleep_df.describe())
