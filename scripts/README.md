# Creating AMY EPW files for simulation

## 1. Unpack NOAA data

The script unpack_noaa_data.py will take .gz files containing NOAA ISD Lite data from the `NOAA_ISD_Lite_Raw` directory
under /inputs and unpack them into a folder called `NOAA_AMY`
in the /outputs directory.

## 2. Analyze NOAA data

The script analyze_noaa_data.py will assess the files in the `NOAA_AMY` folder for:

1. Total number of rows missing
1. Maximum number of consecutive rows missing

and will provide (as applicable):

1. A list of files where the total number of rows missing exceeds a threshold.
   - This is currently set to rule out files where more than 700 (out of 8760 total) entries are missing entirely.
1. A list of files where the maximum consecutive number of rows missing exceeds some threshold.
   - This is currently set to rule out files where more than 48 consecutive entries are missing entirely.
1. A list of files to be used for creating weather files, where neither of the above conditions were met. 
This is called `files_to_convert.csv` and may be altered so that only a single file, or subset of available files, 
are converted to EPW. Simply remove rows for any files that you do not want the next script to process.

These are located in a folder in /outputs called `analyze_noaa_data_ouput`.


# 3. Create AMY EPW file

The script create_amy_epw.py will create EPW files by using information for selected variables from the
NOAA AMY files to replace the values for those same variables in a TMY3 file for the same station number. 
That is, the following 5 variables will consist of AMY data taken from the NOAA ISD Lite dataset with the remainder
of the file consisting of the corresponding WMO station's TMY3 EPW file, taken
from the `EnergyPlus_TMY3_EPW` directory under [canonical_epw_files](../../inputs/canonical_epw_files).

1. dry bulb temperature
1. dew point temperature
1. pressure
1. wind direction
1. wind speed

The function `clean_noaa_df` will accept a dataframe taken from the NOAA AMY
files containing 8760 hourly records, and ensure that in each record a value is
present for all of the hourly timestamps for the variables shown above.

It will also convert these quantities from using NOAA units (described in the
documentation found in [the NOAA ISD Lite folder](../../inputs/canonical_epw_files/NOAA_ISD_Lite_Raw) to
using units consistent with those expected in an EPW file, as shown in [the EPW data dictionary](https://bigladdersoftware.com/epx/docs/8-3/auxiliary-programs/energyplus-weather-file-epw-data-dictionary.html).

## Missing data

Missing data are expected in the observed weather data, either because entire rows are missing, but the cutoff 
thresholds in the previous script were not exceeded, or because one or more variables have missing data even if a
weather observation is present for that time step.

This script will impute missing data as follows:

- 1-6 consecutive missing records: fill with linear interpolation between the surrounding previous time step, *p*, 
and subsequent time step, *s*.
- 7-48 consecutive missing records: obtain the mean value for that variable in that hour of the day for the 
“surrounding month” (previous 2 weeks and subsequent 2 weeks, as available). Use that to fill in missing records except:
  - the first missing time step, *p+1*, will be the mean of the average value calculated as above and the value 
  present in *p*.
  - the last missing time step, *s-1*, will be the mean of the average value calculated as above and the value present 
  in *s*.
  - These exceptions are made to help smooth “jumps” in the weather variable if the day with missing values happens to 
  be different from the monthly average values.
  
## Reading in TMY3 files and writing EPW files
Functions for reading TMY3 files and writing EPW files within this script were taken or adapted from the 
[LAF.py script](https://github.com/SSESLab/laf/blob/master/LAF.py) by Carlo Bianchi at the Site-Specific Energy Systems 
Lab repository.

# Optional: Look up station location

The script identify_wmo_station_location.py contains a function of the same name that accepts a WMO station number (as an integer) and returns the state and county of that WMO station.


