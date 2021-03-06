# fitbit-tracker and fitbit-analysis
A set of modules to interface with the Fitbit tracking website and do some simple data analysis.  Note that this is for personal use and not a replacement for real medical evaluations.  I developed this after getting frustrated with the very simple web application on the fitbit mobile application as well as the website.  I wanted to be able to do more analytics and correlations of the various data that was being collected.  

Rather than writing a new requests based application, I choose to use the fitbit api module created by [ORCAS](https://github.com/orcasgit/python-fitbit).

For the data analyutics tools, I used standard Python data science utilities.  Each new tools is a separate module.  This simplifies dependencies.  I may make them all into a library of thier own at some point.

## Requirements
* Python version: 3 (It may work on 2.7+)
* Python Package: numpy, pandas, matplotlib, seaborn, fitbit, tqdm

## Setup
1.  You need to create and register a fitbit application [here](https://dev.fitbit.com/apps/new).  Make sure that you select that this is a personal application.  If you do not, you will not be able to retrieve intraday data.
1.  Go to the application you just registered and select it.  
1.  Click on the OAuth 2.0 tutorial page.
1.  Click on Implicit Grant Flow
1.  Select the scopes you want to allow (typically heartrate, profile, sleep, activity, settings and profile).
1.  Enter in a time frame for token expiration.  Look at the docs to see the allowed values.
1.  Follow the rest of the instructions on the page so that you get both an *OAuth 2.0 token* and a *refresh token*.
1.  Modify the sample config.json filewith your specific values.  Note that you need to supply all values.  If you do not enter the refresh_token, the application will exit when the token expires.

## Fitbit Tracker Usage 
```
usage: Fitbit Tracker [-h] [-d DEBUG_LEVEL] [-l LOG_FILE] [-o OUTPUT_DIR] [-v]
                      [--days NUMBER_OF_DAYS] [-e END_DATE] [-s START_DATE]
                      (-a | -t COLLECT_TYPE)
                      configfile

Retrieves various information from the Fitbit website.

positional arguments:
  configfile            Name of the configuration file. (default: config.json)

optional arguments:
  -h, --help            show this help message and exit
  -d DEBUG_LEVEL, --debug_level DEBUG_LEVEL
                        Set the debug level [debug info warn] (default: info)
  -l LOG_FILE, --log_file LOG_FILE
                        Set the logfile name. (default: fitbit-tracker.log)
  -o OUTPUT_DIR, --output OUTPUT_DIR
                        output directory to store results files. (default:
                        results)
  -v, --version         prints the version
  --days NUMBER_OF_DAYS
                        number of days to go back
  -e END_DATE, --end_date END_DATE
                        end date to collect data from (yyyy-mm-dd)
  -s START_DATE, --start_date START_DATE
                        start date to collect data from (yyyy-mm-dd)
  -a, --all             collect all the data possible
  -t COLLECT_TYPE, --type COLLECT_TYPE
                        collect only the type of data specified (heartrate,
                        sleep, steps)
```

## Fitbit Analysis Usage 
```
usage: Fitbit Analysis [-h] [-d DEBUG_LEVEL] [-l LOG_FILE] [-o OUTPUT_DIR]
                       [-v] [-e END_DATE] (-a | -t COLLECT_TYPE)
                       (-s START_DATE | --days NUMBER_OF_DAYS | --date DATE_TO_COLLECT)

Analyze Fitbit data generated by the fitbit-tracker.py program.

optional arguments:
  -h, --help            show this help message and exit
  -d DEBUG_LEVEL, --debug_level DEBUG_LEVEL
                        Set the debug level [debug info warn] (default: info)
  -l LOG_FILE, --log_file LOG_FILE
                        Set the logfile name. (default: fitbit-tracker.log)
  -o OUTPUT_DIR, --output OUTPUT_DIR
                        Output directory to store results files. (default:
                        results)
  -v, --version         Prints the version
  -e END_DATE, --end_date END_DATE
                        End date to collect data from (yyyy-mm-dd)
  -a, --all             Analyze all the data possible
  -t COLLECT_TYPE, --type COLLECT_TYPE
                        Analyze only the type of data specified (heartrate,
                        sleep, steps)
  -s START_DATE, --start_date START_DATE
                        Start date to collect data from (yyyy-mm-dd)
  --days NUMBER_OF_DAYS
                        Number of days to go back and analyze
  --date DATE_TO_COLLECT
                        Specifc date to collect for
```

## Files
* fitbit-tracker.py - Collects fitbit data and stores the results into a timeseries csv file(s)
* config.json - JSON configuration file.  Note that this contains secrets so do not store on public systems
* fitbit-analysis.py - Generates basic analysis of the data.

## Acknowledgements
* [Oregon Center for Applied Science - ORCA](https://github.com/orcasgit/python-fitbit) - Fitbit API Python Client Implementation
* [Python Data Science Handbook](https://tanthiamhuat.files.wordpress.com/2018/04/pythondatasciencehandbook.pdf) - Excellent introductory book.

