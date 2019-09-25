# -*- coding: utf-8 -*-
"""Generates analytics for data generated by fitbit-tracker.py

Reads in fitbit data generated by the fitbit-tracker.py program and generates
a series of data insights, graphs, charts and/or tables.

"""
# TODO(dph): Think about ading a configuration file as the options get more complicated
#            with regards to statistics

import argparse
import io
import os
import os.path
import sys
import logging
import logging.handlers
import json

import pandas as pd
import numpy as numpy
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.dates as md
import seaborn as sns
import pandas_profiling

from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

from datetime import datetime
from datetime import date
from datetime import timedelta

# Globals
__AUTHOR__ = 'David Hunter'
__VERSION__ = 'fitbit-analysis ver beta-0.1'
__LOG_NAME__ = 'fitbit-analysis.log'
__TITLE__ = 'fitebit-analysis.py'

def set_command_options():
    """Define command line arguments."""

    usage = 'Analyze Fitbit data generated by the fitbit-tracker.py program.'
    parser = argparse.ArgumentParser(prog='Fitbit Analysis', description=usage,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    type_group = parser.add_mutually_exclusive_group(required=True)
    date_group = parser.add_mutually_exclusive_group(required=True)

    parser.add_argument('--log', '--log_level',
                        help='Set the logging level [debug info warn error] (default: %(default)s)', action='store', dest='log_level', type=str, default='info')
    parser.add_argument('-l', '--log_file', help='Set the logfile name. (default: %(default)s)',
                        action='store', type=str, default='fitbit-tracker.log')
    parser.add_argument('-o', '--output',  help='Output directory to store results files. (default: %(default)s)',
                        action='store', type=str,  dest='output_dir', default='results')
    parser.add_argument('-v', '--version', help='Prints the version',
                        action='version', version=__VERSION__)
    parser.add_argument('-e', '--end_date',  help='End date to analyze data from (yyyy-mm-dd)',
                        action='store', type=str,  dest='end_date')
    msg = 'Set the types of statistics to calculate for the collected data.  The options are min, middle or max.  Note that max will take a long time.'
    parser.add_argument('--stats', help=msg, action='store', dest='stats_to_calc', type=str, default='min')


    type_group.add_argument(
        '-a', '--all', help='Analyze all the data possible', action='store_true')
    type_group.add_argument('-t', '--type', help='Analyze only the type of data specified (heartrate, sleep, steps)',
                            action='store', type=str, dest='collect_type')

    date_group.add_argument('-s', '--start_date',  help='Start date toanalyze data from (yyyy-mm-dd)',
                            action='store', type=str,  dest='start_date')
    date_group.add_argument('--days', help='Number of days to go back and analyze',
                            action='store', type=int, dest='number_of_days')
    date_group.add_argument('--date', help='Specifc date to collect for',
                            action='store', type=str, dest='date_to_collect')
    args = parser.parse_args()
    return(parser)


def get_command_options(parser):
    """ Retrieves the command line options and returns a kv dict """

    args = parser.parse_args()

    fmt = "%(asctime)-15s %(levelname)-8s %(lineno)5d:%(module)s:%(funcName)-25s %(message)s"
    log_file = args.log_file
    options = {'log_file': args.log_file}

    # Set up the logging infrastructure before we do anything.  The default is INFO
    if args.log_level:
        if 'debug' in args.log_level:
            logging.basicConfig(filename=args.log_file, format=fmt, level=logging.DEBUG)
            # logging.basicConfig(level=logging.DEBUG)
            logging.debug('Logging level set to: ' + args.log_level)
        elif 'warn' in args.log_level:
            logging.basicConfig(filename=args.log_file, format=fmt, level=logging.WARNING)
            logging.warning('Logging level set to: ' + args.log_level)
        elif 'error' in args.log_level:
            logging.basicConfig(filename=args.log_file, format=fmt, level=logging.ERROR)
            logging.error('Logging level set to: ' + args.log_level)
        elif 'info' in args.log_level:
            logging.basicConfig(filename=args.log_file, format=fmt, level=logging.INFO)
            logging.info('Logging level set to: ' + args.log_level)
        else:
            logging.basicConfig(filename=args.log_file, format=fmt, level=logging.INFO)
            logging.error('Invalid debug level.  Exiting the program.')
            sys.exit(1)

    if args.all:
        options['analyze_type'] = 'steps heartrate sleep'
    elif args.collect_type:
        options['analyze_type'] = args.collect_type
        logging.info('Analyzing: ' + args.collect_type)
    else:
        logging.error('You need to specify the type of data to analyze or use the -a flag')
        sys.exit(1)

    if ((args.number_of_days and (args.start_date or args.end_date))
            or (args.date_to_collect and (args.start_date or args.end_date))):
        logging.error('Illegal date specifications.  Exiting')
        sys.exit(1)

    elif args.number_of_days:
        if args.number_of_days <= 0:
            logging.error(
                "Number of days needs to be greater than zero.  Exiting")
            sys.exit(1)
        else:
            options['number_of_days'] = args.number_of_days
            logging.info("Number of days previous: " +
                         str(options['number_of_days']))

    elif args.date_to_collect:
        # Collect for a specific day
        if is_valid_date(args.date_to_collect):
            options['date_to_collect'] = args.date_to_collect
            logging.info("Date to collect for: " + str(options['date_to_collect']))
        else:
            print('Invalid date specified.  Exiting.')
            logging.error('Invalid date: ' + str(args.date_to_collect))
            sys.exit(1)

    elif args.start_date and args.end_date:
        if not is_valid_date(args.start_date):
            print('Invalid start date specified.  Exiting.')
            logging.error('Invalid start date: ' + str(args.start_date))
            sys.exit(1)
        elif not is_valid_date(args.end_date):
            print('Invalid end date specified.  Exiting.')
            logging.error('Invalid end date: ' + str(args.end_date))
            sys.exit(1)
        else:
            options['start_date'] = args.start_date
            options['end_date'] = args.end_date
            logging.info('Start date: ' + args.start_date)
            logging.info('End date: ' + args.end_date)
            if args.start_date > args.end_date:
                logging.error("Start date is after end date. Exiting.")
                sys.exit(1)

    else:
        # Start and end date not specified.
        logging.error(
            'Both start and end dates need to be specified. Exiting.')
        sys.exit(1)

    if not os.path.isdir(args.output_dir):
        logging.error('Directory does not exist')
        sys.exit(1)
    else:
        options['output_dir'] = args.output_dir

    logging.debug(json.dumps(options))
    return(options)

def is_valid_date(date_to_check):
  """ Checks to see if the date is valid """
  year,month,day = date_to_check.split('-',3)
  try :
    date(int(year), int(month), int(day))
  except ValueError :
    return(False)
  return(True)

def get_dataframe(fname):
    """ Reads in a file generated by fitbit-tracker, converts the index into a timedelta value
        and returns the results in a dataframe """
    df = pd.read_csv(fname, sep=',', header=0, index_col=0, skip_blank_lines=True, dtype={1: 'int32'})
    # TODO(dph): Need to figure out if we can just use the timedelta as an index vs the whole date.
    #            for now we just take the date the dataframe is created.
    #df.index = pd.TimedeltaIndex(df.index)
    df.index = pd.DatetimeIndex(df.index)
    return(df)

def get_all_file_list(dir_name, fragment):
    """ Gets a list of files within a directory based on a string in the filename """
    if os.path.isdir(dir_name):
        all_files = []
        list_of_files = os.listdir(dir_name)
        for file_name in list_of_files:
            if fragment in file_name:
                full_path_name = os.path.join(dir_name, file_name)
                all_files.append(full_path_name)
        return(all_files)
    else:
        logging.error('Invalid directory provided in get_all_file_list function.  Exiting')
        exit(1)

def date_range(start, end):
  """ Returns a list of dates """
  r = (end+timedelta(days=1)-start).days
  return[start+timedelta(days=i) for i in range(r)]

def get_date_frag(options):
  """ Creates a list of file fragment using the date """

  if 'end_date' in options and 'start_date' in options:
      start_date = datetime.strptime(options['start_date'], '%Y-%m-%d')
      end_date = datetime.strptime(options['end_date'], '%Y-%m-%d')
      number_of_days_requested = (end_date - start_date).days
      logging.info('Startdate:' + str(start_date))
      logging.info('Enddate:' + str(end_date))
      logging.info('Days requested vale: ' + str(number_of_days_requested))
      logging.info('Number of interger days requested: ' +
                   str(number_of_days_requested))
      date_list = date_range(start_date, end_date)
      logging.debug(date_list)

  elif 'number_of_days' in options:
        # Use the --days option
        today = datetime.today()
        # TODO(dph): The line below throws the "FutureWarning: Addition/subtraction of
        # integers and integer-arrays to DatetimeArray is deprecated, will be removed
        # in a future version.  Instead of adding/subtracting `n`, use `n * self.freq`
        start_date = today - timedelta(days=options['number_of_days'])
        start_date_str = datetime.strftime(start_date, "%Y-%m-%d")
        number_of_days_requested = 1
        logging.info('Collect data for: ' + str(start_date))
        date_list = date_range(start_date, start_date)
        logging.debug(date_list)

  elif 'date_to_collect' in options:
        start_date = datetime.strptime(options['date_to_collect'], '%Y-%m-%d')
        start_date_str = options['date_to_collect']
        logging.info('Collect for the specific date:' + start_date_str)
        number_of_days_requested = 1
        date_list = date_range(start_date, start_date)
        logging.debug(date_list)
  else:
        logging.error('No date specified.  Exiting')
        sys.exit(1)

  date_frag_list = list()
  for date in date_list:
      date_frag_list.append(datetime.strftime(date, '%Y-%m-%d'))
  return(date_frag_list)

def create_index_file(fname, start, end, freq):
    """ Creates an dataframe with an time index and stores it in the passed filename """

    rng = pd.date_range(start=start, end=end, freq=freq)
    #base_df = pd.DataFrame({'Time': rng.strftime('%H:%M:%S'), 'Day': '0'})
    #base_df.to_csv(fname, columns=['Time', 'Index'], header=True, index=False)
    base_df = pd.DataFrame({'Time': rng.strftime('%H:%M:%S')})
    base_df.to_csv(fname, columns=['Time'], header=True, index=False)

def interpolate_gaps(values, limit=None):
    """
    Fill gaps using linear interpolation, optionally only fill gaps up to a
    size of `limit`.
    """
    values = np.asarray(values)
    i = np.arange(values.size)
    valid = np.isfinite(values)
    filled = np.interp(i, i[valid], values[valid])

    if limit is not None:
        invalid = ~valid
        for n in range(1, limit+1):
            invalid[:-n] &= invalid[n:]
        filled[invalid] = np.nan

    return filled

##### MAIN PROG STARTS HERE #####
if __name__ == '__main__':
  parser = set_command_options()
  options = get_command_options(parser)
  frag_list = get_date_frag(options)
  index_file = options['output_dir'] + '/intraday_index.csv'

  # Using the date fragments, generate the list of files to retrieve
  file_list = list()
  for frag in frag_list:
    if 'heartrate' in options['analyze_type']:
      f1 = options['output_dir'] + '/hr_intraday_' + str(frag) + '.csv'
    elif 'steps' in options['analyze_type']:
      f1 = options['output_dir'] + '/steps_intraday_' + str(frag) + '.csv'
    elif 'sleep' in options['analyze_dir']:
      f1 = options['output_dir'] + '/sleep_day_' + str(frag) + '.csv'
    if os.path.exists(f1):
      file_list.append(f1)

  # If no files match, just report and exit.
  if len(file_list) == 0:
      msg = 'No matching files find for request.'
      print(msg)
      logging.warning(msg)
      exit(-1)

  logging.debug(file_list)
  logging.info('The number of elements in file_list is: ' + str(len(file_list)))
  logging.info('The number of elements in frag_list is: ' + str(len(frag_list)))

  # TODO(dph): Finish implmenting the case to calculate all the analysis for all
  # of the available data files in the directory indicated.
  # Get data for all the dates....
  #file_list = get_all_file_list('./results', 'hr_intraday_')

  # TODO(dph): Make this simplier and not dependent upon the external index file
  #            Maybe just add it as a column to a dataframe and then set that column
  #            as the index?

  # Generate an index that consists of HH:MM:SS and convert it to the timedelta index.
  # This is used to ensure that all possible index values in the day can be captured
  # as the FitBit second intervals can vary day to day.
  create_index_file(index_file, start='00:00:00', end='23:59:59', freq='S')
  merge_df = get_dataframe(index_file)
  summary_df = get_dataframe(index_file)

  for fname in file_list:
    hr_df = get_dataframe(fname)
    merge_df = pd.merge(merge_df, hr_df, left_index=True, right_index=True, how='left')
  merge_df.index.name = 'Time'

  # TODO(dph): Keep track of the dropped dates and report them in the log.
  # Look for any days that have all NaaN values and just drop them.  This is best rather than
  # adding interpolated data in the next step.

  # TODO(dph): Make this an option in cases where we want just the sampled values.
  # For NaaN values, we will interpolate their values based on a linear algorithium.  While this
  # may not be 100% accurate, it does assume that the pace of change is realtively equal between
  # sampled values.
  # Note:  If we interpolate along the column (axis=1) then we will get go along the lines of
  # assuming that the next value (fwd or bckwd) would be the logical value.  If we interpolate
  # along the row, aka: time based (axis=0), we assume that more often than not the missing
  # value is relatively constant across time.
  # TODO(dph): Explore the use of the limit_area, limit and limit_direction arguments to see if
  #            what the differences are.  Alternatively make it an optional.

  print(merge_df.head(50))
  merge_df.interpolate(method='linear', axis=0, inplace=True, limit_direction='both')
  print(merge_df.head(50))

  # Calculate some statistics for the rows and store it in a new dataframe
  summary_df['Mean'] = merge_df.mean(axis=1)
  summary_df['Median'] = merge_df.median(axis=1)
  summary_df['Min'] = merge_df.min(axis=1)
  summary_df['Max'] = merge_df.max(axis=1)
  summary_df['StdDev'] = merge_df.std(axis=1)

  # Generate a profile of the dataframe. Note that this takes a long time and
  # should be shifted to an option vs all the time.
  #profile = merge_df.profile_report(title='Merged Dataframe Report')
  #profile.to_file(output='profile_report.html')

  plt.plot(x=merge_df[0], y=merge_df[1:] )
  #plt.plot(summary_df)
  # Finally show the plots/charts.  Only call this at the end.
  plt.show()

  # To do a simple analysis, add the sleep data into the merged dataframe to see what type of sleep was occuring during the heartrate
