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
# TODO(dph) Need to add in try/except error handeling when a day contains no data.

# Imports
import fitbit
import inspect
import argparse
import json
import os
import os.path
import sys
import requests
import pandas as pandas
import logging
import logging.handlers

from os import path
from datetime import datetime 
from datetime import date
from datetime import timedelta

# Globals
__AUTHOR__ = 'David Hunter'
__VERSION__ = 'fitbit-tracker ver beta-0.5'
__LOG_NAME__ = 'fitbit-tracker.log'
__TITLE__ = 'fitebit-tracker.py'

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
  group = parser.add_mutually_exclusive_group(required=True)
  
  parser.add_argument('configfile', help='Name of the configuration file. (default: %(default)s)', type=str, default='config.json')
  parser.add_argument('-d', '--debug_level', help='Set the debug level [debug info warn] (default: %(default)s)', action='store', type=str, default='info')
  parser.add_argument('-l', '--log_file', help='Set the logfile name. (default: %(default)s)', action='store', type=str, default='fitbit-tracker.log')
  parser.add_argument('-o', '--output',  help='output directory to store results files. (default: %(default)s)', action='store', type=str,  dest='output_dir', default='results')                    
  parser.add_argument('-v', '--version', help='prints the version', action='version', version=__VERSION__)
  parser.add_argument('--days', help='number of days to go back', action='store', type=int, dest='number_of_days')
  parser.add_argument('-e', '--end_date',  help='end date to collect data from (yyyy-mm-dd)', action='store', type=str,  dest='end_date')                    
  parser.add_argument('-s', '--start_date',  help='start date to collect data from (yyyy-mm-dd)', action='store', type=str,  dest='start_date')                    

  group.add_argument('-a', '--all', help='collect all the data possible', action='store_true')
  group.add_argument('-t', '--type', help='collect only the type of data specified (heartrate, sleep, steps)', action='store', type=str, dest='collect_type')


  args = parser.parse_args()
  return(parser);

def get_command_options(parser):
  "Retrieves the command line options and returns a kv dict"
  args = parser.parse_args()
  fmt = "%(asctime)-15s %(levelname)-8s %(message)s"
  log_file = args.log_file
  options = {'log_file' : args.log_file}
  logging.basicConfig(filename=args.log_file, format=fmt, level=logging.INFO)
  
  # Retrieve the data type(s) to collect.
  if args.all:
    options['collect_type'] = 'steps heartrate sleep'
  elif args.collect_type:
    options['collect_type'] = args.collect_type
    func = inspect.currentframe()
    logging.info('Collecting information for: '+ args.collect_type)
  else:
    logging.warning('You need to specify the type of data to collect or use the -a flag')
    sys.exit(1)
  
  # Set the desired logging level
  if args.debug_level:
    if 'debug' in args.debug_level:
      logging.basicConfig(level=logging.DEBUG)
    if 'warn' in args.debug_level:
      logging.basicConfig(level=logging.WARNING)
    elif 'info' in args.debug_level:
      logging.basicConfig(level=logging.INFO)
    elif 'error' in args.debug_level:
      logging.basicConfig(level=logging.ERROR)
    else:
      logging.basicConfig(level=logging.ERROR)
      logging.error('Invalid debug level.  Exiting the program.')
      sys.exit(1)
  
  # Use the specified configuration file.  There is no default.
  if args.configfile:
    if path.exists(args.configfile):
      options['config_file'] = args.configfile
    else:
      logging.error("Configuration file does not exist.  Exiting.")
      sys.exit(1)
  
  # Retrieve the the day(s) to collect data for
  if args.number_of_days and (args.start_date or args.end_date ):
    logging.error('You can not specify both a start/end date and number of days.  Exiting')
    sys.exit(1)

  elif args.number_of_days:
    # Use number of days before today
    if args.number_of_days <= 0:
      logging.error("Number of days needs to be greater than zero.  Exiting")
      sys.exit(1)
    else:
      options['number_of_days'] = args.number_of_days
      logging.info("Number of days previous: " + str(options['number_of_days']))
  
  elif args.start_date and args.end_date:
    # Use start and end dates
    options['start_date'] = args.start_date
    options['end_date'] = args.end_date
    logging.info('Start date: ' + args.start_date)
    logging.info('End date: ' + args.end_date)
    if args.start_date > args.end_date:
      logging.error("Start date is after end date.  Exiting.")
      sys.exit(1)
  else:
    # Start and end date not specified.
    logging.error('Both start and end dates need to be specified.  Exiting.')
    sys.exit(1)

  if not os.path.isdir(args.output_dir):
    logging.error('Directory does not exist')
    sys.exit(1)
  else:
    options['output_dir'] = args.output_dir

  logging.info(json.dumps(options))
  return(options)

### MAIN PROGRAM STARTS HERE ###

parser = set_command_options()
options = get_command_options(parser)

with open(options['config_file']) as json_config_file:
  data = json.load(json_config_file)
  
# Connect to the fitbit server using oauth2 See the page https://dev.fitbit.com/build/reference/web-api/oauth2/
if data['access_token'] == '':
  print("No access token found.  Please generate and place in the configuration file.")
  logging.error('No access token found.  Exiting.')
  sys.exit(1)

# TODO(dph): Modify this to account for when the token expires
try:
  authd_client = fitbit.Fitbit(data['client_id'], data['client_secret'], access_token=data['access_token'])
  authd_client2 = fitbit.Fitbit(data['client_id'], data['client_secret'], oauth2=True, access_token=data['access_token'], refresh_token=data['refresh_token'])
except auth.exceptions.HTTPUnauthorized:
  print('Please provide latest refresh and access tokens for oauth2. Exiting program.')
  logging.error('Please provide latest refresh and access tokens for oauth2. Exiting program.')
  sys.exit(1)

# Note that that there is a limit of 150 api requests per hour. If the
# requested number of days will exceed that, message back to the caller and exit.
request_limit = 150
num_types = 0
if 'heartrate' in options['collect_type']: num_types += 1
if 'sleep' in options['collect_type']: num_types += 1
if 'steps' in options['collect_type']: num_types += 1
max_days = int(request_limit/num_types)
logging.info('Max days: ' + str(max_days))
number_of_days_requested_int = 1

if 'end_date' in options and 'start_date' in options:
  # Get the start date and number of days to requested.  Ensure it does not exceed the api limit/hr
  # Note that this assumes there have been no other api requests during the hour. 
  start_date = datetime.strptime(options['start_date'], '%Y-%m-%d')
  end_date = datetime.strptime(options['end_date'], '%Y-%m-%d')
  number_of_days_requested = end_date - start_date
  number_of_days_requested_int = getattr(number_of_days_requested, 'days')

  logging.info('Startdate:' + str(start_date))
  logging.info('Enddate:' + str(end_date))
  logging.info('Days requested vale: ' + str(number_of_days_requested))
  logging.info('Number of interger days requested: ' + str(number_of_days_requested_int))

  if number_of_days_requested_int > max_days:
    logging.error('Requested days exceed number calls per hour.  Exiting')
    sys.exit(1)

elif 'number_of_days' in options:
  # Use the --days option
  today = datetime.today()
  start_date = today - timedelta(days=options['number_of_days'])
  start_date_str = datetime.strftime(start_date,"%Y-%m-%d")
  logging.info('Collect data for: ' + str(start_date))

else:
  logging.error('No date specified.  Exiting')
  sys.exit(1)

# Iterrate trhough the days.  If we just have a single date, start there 
# and use the date specified.
print('number_of_days_requested = ' + str(number_of_days_requested_int))
for d in range(0, number_of_days_requested_int):
  start_date_str = str(start_date.strftime('%Y-%m-%d'))
  start_date = start_date + timedelta(days=1)

  try:
    if 'heartrate' in options['collect_type'] or 'all' in options['collect_type']:
      heartrate_file = options['output_dir'] + '\\' + 'hr_intraday_' + start_date_str + '.csv'
      heartrate_df = get_heartrate(oauth_client=authd_client2, start_date=start_date_str, time_interval='1sec', results_file=heartrate_file)
      print(heartrate_df.describe())
  
    if 'steps' in options['collect_type'] or 'all' in options['collect_type']:
      steps_file = options['output_dir'] + '\\' + 'steps_intraday_' + start_date_str + '.csv'
      steps_df = get_steps(oauth_client=authd_client2, start_date=start_date_str, time_interval='15min', results_file=steps_file)
      print(steps_df.describe())

    if 'sleep' in options['collect_type'] or 'all' in options['collect_type']:
      sleep_file = options['output_dir'] + '\\' + 'sleep_day_' + start_date_str + '.csv'
      sleep_df = get_sleep(oauth_client=authd_client2, start_date=start_date, results_file=sleep_file)
      print(sleep_df.describe())

  # Try and recover from exceptions and if not, gracefully report and exit.  
  
  except fitbit.exceptions.HTTPBadRequest:
    # Response code = 400.
    print('An unhandled exception.  Exiting program.')
    logging.error('An unhandled exception.  Exiting program.')
    sys.exit(1)

  except fitbit.exceptions.HTTPUnauthorized:
    # Response code = 401, the token has expired, exit for now.
    # TODO(dph): Enable the ability to refresh the token automatically.
    print('Please provide latest refresh and access tokens for oauth2. Exiting program.')
    logging.error('Please provide latest refresh and access tokens for oauth2. Exiting program.')
    sys.exit(1)
  
  except fitbit.exceptions.HTTPForbidden:
    # Response code = 403.
    print('You are not allowed to excute the function requested.  Exiting program.')
    logging.error('You are not allowed to excute the function requested.  Exiting program.')
    sys.exit(1)
  
  except fitbit.exceptions.HTTPNotFound:
    #  Response code = 404.
    print('Requested function or data not found.  Exiting program.')
    logging.error('Requested function or data not found.  Exiting program.')
    sys.exit(1)

  except fitbit.exceptions.HTTPConflict:
    #  Response code = 409.
    print('Conflict when creating resources.  Exiting program.')
    logging.error('Conflict when creating resources.  Exiting program.')
    sys.exit(1)

  except fitbit.exceptions.HTTPTooManyRequests:
    #  Response code = 429.
    print('Rate limit exceeded. Rerun program after 1 hour. Exiting program.')
    print('Stopped at: ' + start_date_str)
    logging.error('Rate limit exceeded. Rerun program after 1 hour. Exiting program.')
    logging.info('Stopped at: ' + start_date_str)
    sys.exit(1)
  
  except fitbit.exceptions.HTTPServerError:
    # Response code = 500.
    print('A generic error was returned.  Exiting program.')
    logging.error('A generic error was returned.  Exiting program.')
    sys.exit(1)

  


