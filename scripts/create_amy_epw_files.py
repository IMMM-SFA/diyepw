import os
import glob
import csv
import numpy as np
import pandas as pd
import argparse

####################################################################################################################
# Clean NOAA ISD Lite dataframe
####################################################################################################################

def clean_noaa_df(df):
    """Add headings to a NOAA ISD Lite formatted dataframe, convert year-month-day-hour columns to a timestamp,
    set the timestamp as index, and make sure each hour of the year has a timestamp, regardless of whether there are
    any observations in that hour. Drop columns for observations that won't be used in populating the EPW files.
    (Caution: only designed to process non-leap years.)"""

    # Assign column headings according to NOAA ISD Lite information.
    list_of_columns = ["Year", "Month", "Day", "Hour", "Air_Temperature",
                       "Dew_Point_Temperature", "Sea_Level_Pressure", "Wind_Direction",
                       "Wind_Speed", "Sky_Condition_Total_Coverage_Code",
                       "Liquid_Precipitation_Depth_Dimension_1H", "Liquid_Precipitation_Depth_Dimension_6H"]
    df.columns = list_of_columns
    df_year = str(df['Year'][0])  # Year is the same for all entries, so just get one

    # Take year-month-day-hour columns and convert to datetime stamps.
    df['obs_timestamps'] = pd.to_datetime(pd.DataFrame({'year': df['Year'],
                                                        'month': df['Month'],
                                                        'day': df['Day'],
                                                        'hour': df['Hour']}))

    # Remove unnecessary year, month, day, hour columns and columns for variables not used to fill EPW.
    df = df.drop(columns=['Year', 'Month', 'Day', 'Hour', 'Sky_Condition_Total_Coverage_Code',
                          'Liquid_Precipitation_Depth_Dimension_1H', 'Liquid_Precipitation_Depth_Dimension_6H'])

    # Create series of continuous timestamp values for that year
    all_timestamps = pd.date_range(df_year + '-01-01 00:00:00', df_year + '-12-31 23:00:00', freq='H')

    # Merge to one dataframe containing all continuous timestamp values.
    all_timestamps = pd.DataFrame(all_timestamps, columns=['timestamp'])
    df = pd.merge(all_timestamps, df, how='left', left_on='timestamp', right_on='obs_timestamps')
    df = df.drop(columns=['obs_timestamps'])

    # Set timestamps as index.
    df = df.set_index('timestamp')

    # Return the cleaned data frame.
    return df

####################################################################################################################
# Replace missing value codes with NAs
####################################################################################################################

def replace_series_value(series, to_replace, replacement_value):
    """Take a Pandas Series and replace a particular value with a replacement value.
    This provides similar functionality to .replace(), which has an issue when replacing
    values in slices with heterogeneous data types.
    (Related issue: https://github.com/pandas-dev/pandas/issues/29813)"""

    replaceindex = series[series==to_replace].index
    series[replaceindex] = replacement_value
    return series


####################################################################################################################
# Convert sea level pressure from NOAA ISD Lite data to station pressure
####################################################################################################################

def convert_to_station_pressure(Pa, h_m) -> object:
    """Return the atmospheric station pressure in Pa given sea level pressure in hPa*10 and station elevation in m."""

    # convert (or keep) pressure and elevation inputs as floats
    Pa = float(Pa)
    h_m = float(h_m)

    # convert from hectopascals*10 to inHg
    Pa_inHg = Pa/10 * 0.029529983071445

    # calculate station pressure according to formula from https://www.weather.gov/epz/wxcalc_stationpressure
    Pstn_inHg = Pa_inHg * ((288 - 0.0065*h_m)/288)**5.2561

    # convert from inHg to Pa
    Pstn = Pstn_inHg * 3386.389

    # The valid value check here has been commented out as the values are now checked separately below.
    # # If the calculated atmospheric station pressure is outside the EPW limits
    # if (Pstn < 31000) or (Pstn > 120000):
    #     # per EPW data dictionary:
    #     # https://bigladdersoftware.com/epx/docs/8-3/auxiliary-programs/energyplus-weather-file-epw-data-dictionary.html
    #
    #     # print('Station pressure outside of EPW bounds: min 31000, max 120000 \nCalculated pressure in Pa: ' + str(Pstn)
    #     #       + '\nStation_year: ' + station_year + '\nNOAA pressure in hectopascals: ' + str(Pa))
    #
    #     # Assign the missing value for EPW-formatted files for atmospheric station pressure.
    #     Pstn = 999999

    return Pstn


# from https://github.com/SSESLab/laf/blob/master/LAF.py
####################################################################################################################
# Read file
####################################################################################################################
def read_datafile(file_name, skiplines):
    data = np.genfromtxt(file_name, delimiter=',', skip_header=skiplines)
    return data


# adapted from https://github.com/SSESLab/laf/blob/master/LAF.py
####################################################################################################################
# Read TMY3 file
####################################################################################################################
def read_tmy3(tmy3_name):
    if len(tmy3_name) > 0:
        ############################
        # Read TMY3 header
        ############################
        f = open(tmy3_name)
        global header
        header = []
        for i in range(0, 8):
            line = f.readline()
            header.append(line)
        f.close()

        f2 = open(tmy3_name, 'rt')
        first_line = next(csv.reader(f2))
        for i in range(0, 4):
            next(csv.reader(f2))
        comm_line = next(csv.reader(f2))
        f2.close()
        #
        global lat, long, DS, City, State, Country, elev, comm1, tz, refy
        lat = first_line[6]
        long = first_line[7]
        DS = 'NOAA_TMY3' # Data Source and Uncertainty Flags
        City = first_line[1]
        State = first_line[2]
        Country = first_line[3]
        # WMO field in EPW corresponds to station_number_string
        elev = first_line[9] # station elevation in meters
        comm1 = comm_line[1]
        tz = first_line[8] # time zone relative to GMT
        ############################
        # Read TMY3 data
        ############################
        data = read_datafile(tmy3_name, 8)
        global Y, M, D, HH, MM, Tdb, Tdew, RH, Patm, ExHorRad, ExDirNormRad, HorIR, GHRad, DNRad, DHRad, GHIll, DNIll, DHIll
        global HorIR, GHRad, GHIll, DNIll, DHIll, ZenLum, Wdir, Wspeed, TotSkyCover, OpSkyCover, Visib, CeilH, PrecWater
        global AerOptDepth, SnowDepth, DSLS, Albedo, LiqPrecDepth, LiqPrecQuant, PresWeathObs, PresWeathCodes

        Y = data[:, 0]
        M = data[:, 1]
        D = data[:, 2]
        HH = data[:, 3]
        MM = data[:, 4]
        Tdb = data[:, 6]
        Tdew = data[:, 7]
        RH = data[:, 8]
        Patm = data[:, 9]
        ExHorRad = data[:, 10]
        ExDirNormRad = data[:, 11]
        HorIR = data[:, 12]
        GHRad = data[:, 13]
        DNRad = data[:, 14]
        DHRad = data[:, 15]
        GHIll = data[:, 16]
        DNIll = data[:, 17]
        DHIll = data[:, 18]
        ZenLum = data[:, 19]
        Wdir = data[:, 20]
        Wspeed = data[:, 21]
        TotSkyCover = data[:, 22]
        OpSkyCover = data[:, 23]
        Visib = data[:, 24]
        CeilH = data[:, 25]
        PresWeathObs = data[:, 26]
        PresWeathCodes = data[:, 27]
        PrecWater = data[:, 28]
        AerOptDepth = data[:, 29]
        SnowDepth = data[:, 30]
        DSLS = data[:, 31]
        Albedo = data[:, 32]
        LiqPrecDepth = data[:, 33]
        LiqPrecQuant = data[:, 34]
        return


# adapted from https://github.com/SSESLab/laf/blob/master/LAF.py
####################################################################################################################
# Write new EPW file
####################################################################################################################
def write_epw(save_path):
    filename_epw = '/' + Country + '_' + State + '_' + City + '.' + station_number_string + '_AMY_' + \
             year_string + '.epw'
    filename_epw = filename_epw.replace(' ', '-')
    OPFILE = save_path + filename_epw
    ofile = open(OPFILE, 'w', newline='')
    line1 = 'LOCATION,' + City + ',' + State + ',' + Country + ',customized weather file,' + station_number_string + \
            ',' + str(lat) + ',' + str(long) + ',' + str(tz) + ',' + str(elev) + '\n'
    ofile.write(line1)
    ofile.write(header[1])
    ofile.write(header[2])
    ofile.write(header[3])
    ofile.write(header[4])
    ofile.write('COMMENTS 1, ' + str(comm1) + '\n')
    ofile.write('COMMENTS 2, TMY3 data from energyplus.net/weather supplemented with NOAA ISD Lite data from '
                'https://www1.ncdc.noaa.gov/pub/data/noaa/isd-lite/ for an actual meteorological year (AMY)\n')
    ofile.write('DATA PERIODS,1,1,Data,' + day_name + ', 1/1, 12/31\n')

    writer = csv.writer(ofile, delimiter=',')

    for i in range(0, 8760):
        row = [int(Y[i]), int(M[i]), int(D[i]), int(HH[i]), int(MM[i]), DS,
               Tdb[i], Tdew[i], RH[i], Patm[i], ExHorRad[i], ExDirNormRad[i], HorIR[i],
               GHRad[i], DNRad[i], DHRad[i], GHIll[i], DNIll[i], DHIll[i], ZenLum[i],
               Wdir[i], Wspeed[i], TotSkyCover[i], OpSkyCover[i], Visib[i], CeilH[i],
               PresWeathObs[i], PresWeathCodes[i], PrecWater[i], AerOptDepth[i], SnowDepth[i],
               DSLS[i], Albedo[i], LiqPrecDepth[i], LiqPrecQuant[i]]
        writer.writerow(row)
    ofile.close()


####################################################################################################################
# START
####################################################################################################################

# Set relative path for where new EPW files should be saved.
amy_epw_file_out_path = '../outputs/AMY_combined_NOAA_TMY3_EPW'

# Set relative path for non-EPW output items produced by this script.
create_out_path  = '../outputs/create_amy_epw_files_output'

# Provide the relative path to list of WMO stations for which new AMY EPW files should be created.
path_to_station_list = '../outputs/analyze_noaa_data_output/files_to_convert.csv'

parser = argparse.ArgumentParser(
    description=f"""
        Generate epw files based on the files generated by unpack_noaa_data.py and analyze_noaa_data.py, which must
        be called prior to this script. The generated files will be written to {amy_epw_file_out_path}
    """
)
parser.add_argument('--max-records-to-interpolate',
                    default=6,
                    type=int,
                    help='The maximum number of consecutive records to interpolate.')

# TODO: Add handling for this argument
parser.add_argument('--max-records-to-impute',
                    default=48,
                    type=int,
                    help='The maximum number of records to impute.')
args = parser.parse_args()

# Read in list of WMO stations for which new AMY EPW files should be created.
station_list = pd.read_csv(path_to_station_list)
station_list = station_list[station_list.columns[0]]

# TODO: should maybe wrap this in an if statement to confirm that station_list is pointing to something
print('Read in station list.')

# Initialize the df to hold station-years for files that violate EnergyPlus valid value criteria.
epw_max_or_min_violations = pd.DataFrame(columns=['file',
                                                  'weather_variable',
                                                  'max_or_min',
                                                  'limit_value',
                                                  'extreme_observed_value'])
epw_counter = 0

# Initialize the df to hold station-years for NOAA files that were not converted to an EPW.
no_epw = pd.DataFrame(columns=['file'])
no_counter = 0

# Iterate through stations in the list.
for idx, station_year in enumerate(station_list, start=1):

    print("Processing", station_year, "(", idx, "/", len(station_list),  ")")

    try:

        # Grab the relative path to the unpacked NOAA AMY file for the station.
        noaa_amy_info_path = os.path.join('../outputs/NOAA_AMY', station_year)

        # Grab the station number from the station_year string.
        station_number_string = station_year.split("-")[0]

        # Grab the year from the station_year string.
        year_string = station_year.split("-")[-1]

        # Convert year to float
        year = float(year_string)

        # Grab the relative path to the EPW file corresponding to that station.
        tmy3_epw_file_path = glob.glob('../inputs/Energy_Plus_TMY3_EPW/*.'
                                       + station_number_string + '_TMY3.epw')
        tmy3_epw_file_path = tmy3_epw_file_path[0]

        # Read in the NOAA AMY file for the station.
        noaa_df = pd.read_csv(noaa_amy_info_path,
                              delim_whitespace=True,
                              header=None)

        # Clean the NOAA AMY data frame for the year of interest.
        noaa_df = clean_noaa_df(noaa_df)

        # Save the first timestamp for that year.
        start_timestamp = noaa_df.index[0]

        # Read in the corresponding TMY3 EPW file.
        read_tmy3(tmy3_epw_file_path)

        # Identify the time zone shift as an integer.
        tz_shift = int(float(tz))

        # Identify the number of time steps to be obtained from the subsequent year's NOAA file.
        abs_time_steps = abs(tz_shift)

        # Identify the name of the subsequent year's NOAA file.
        year_s_string = str(int(year) + 1)

        # Grab the relative path to the NOAA AMY file for the subsequent year.
        glob_string = '../outputs/NOAA_AMY/' + station_number_string + '*' + year_s_string
        noaa_amy_s_info_path = glob.glob(glob_string)
        if len(noaa_amy_s_info_path) == 0:
            raise Exception("Couldn't load subsequent year's data: no file was found matching '" + glob_string + "'")
        noaa_amy_s_info_path = noaa_amy_s_info_path[0]

        # Read in the NOAA AMY file for the station for the subsequent year.
        noaa_df_s = pd.read_csv(noaa_amy_s_info_path,
                              delim_whitespace=True,
                              header=None)

        # Clean the NOAA AMY data frame for the subsequent year.
        noaa_df_s = clean_noaa_df(noaa_df_s)

        # Grab the appropriate number of time steps for the subsequent year.
        # TODO: Don't need to process all of these time steps in clean_noaa_df function.
        noaa_df_s = noaa_df_s.head(abs_time_steps)

        # Append the NOAA dataframe for the subsequent year to the dataframe for the year of interest.
        noaa_df = noaa_df.append(noaa_df_s)

        # Shift the timestamp (index) to match the time zone of the WMO station.
        noaa_df = noaa_df.shift(periods=tz_shift, freq='H')

        # Remove time steps that aren't applicable to the year of interest
        noaa_df = noaa_df[noaa_df.index >= start_timestamp]

        for column in range(0, 5):

            colname = noaa_df.columns[column]

            # Take a series out for the variable column we're working with.
            var_series = noaa_df.iloc[:,column].copy()

            # Replace -9999 values (missing values in NOAA's ISD Lite format) with NaNs.
            var_series = replace_series_value(var_series, -9999, None)

            # Fill in up to 6 consecutive missing values by linear interpolation.
            var_series.interpolate(method='linear', limit=args.max_records_to_interpolate, inplace=True)

            # Start a dataframe that will be used to do the replacement of groups of consecutive missing values.
            var_df = pd.DataFrame(var_series)
            var_df['needs_replacement'] = pd.isnull(var_series)
            var_df['replacement_value'] = None

            replace_list = var_df.index[var_df['needs_replacement'] == True].tolist()

            for ts in replace_list:

                # List to store the variable values
                values = list([])

                # Grab the values of the same variable in the same hour for 2 weeks preceding and 2 weeks after.
                # Note: Will use fewer than 4 weeks of data if it extends before or after the file's calendar year.
                for mult in range(-14, 15):
                    idx = ts - mult*pd.Timedelta('24h')
                    if idx < noaa_df.index[0]:
                        continue
                    elif idx > noaa_df.index[-1]:
                        break
                    else:
                        val = var_df.loc[idx, colname]
                    values.append(val)

                # Take the mean of the values pulled. Will ignore NaNs.
                var_df.loc[ts, 'replacement_value'] = pd.Series(values, dtype=np.float64).mean()

                # Average out the first and last replacement values in a sequence of missing values with
                # the previous and subsequent observed values to smooth the transitions between observed and replaced.

                p_ts = ts - pd.Timedelta('1h')
                if p_ts < noaa_df.index[0]:
                    var_df.loc[ts, 'replacement_value'] = var_df.loc[ts, 'replacement_value']
                elif not var_df.loc[p_ts, 'needs_replacement']:
                    var_df.loc[ts, 'replacement_value'] = (var_df.loc[ts, 'replacement_value']
                                                           + var_df.loc[p_ts, colname]) / 2

                s_ts = ts + pd.Timedelta('1h')
                if s_ts > noaa_df.index[-1]:
                    var_df.loc[ts, 'replacement_value'] = var_df.loc[ts, 'replacement_value']
                elif not var_df.loc[s_ts, 'needs_replacement']:
                    var_df.loc[ts, 'replacement_value'] = (var_df.loc[ts, 'replacement_value']
                                                           + var_df.loc[s_ts, colname]) / 2

                # Move the replacement values into the variable values column.
                var_df.loc[ts, colname] = var_df.loc[ts, 'replacement_value']

            # Drop unnecessary columns.
            var_df = var_df.drop(columns=['needs_replacement', 'replacement_value'])

            # Save the filled-in variable column to the NOAA AMY info dataframe.
            noaa_df[colname] = var_df[colname]

        # Convert air (dry bulb) temperature in NOAA df to degrees C.
        noaa_df['Air_Temperature'] = noaa_df['Air_Temperature'] / 10

        # Convert dew point temperature in NOAA df to degrees C.
        noaa_df['Dew_Point_Temperature'] = noaa_df['Dew_Point_Temperature'] / 10

        # Initialize new column for station pressure (not strictly necessary)
        noaa_df['Station_Pressure'] = None

        # Convert sea level pressure in NOAA df to atmospheric station pressure in Pa.
        for index in noaa_df.index:
            stp = convert_to_station_pressure(noaa_df['Sea_Level_Pressure'][index], elev)
            noaa_df.loc[index, 'Station_Pressure'] = stp

        # Remove unnecessary sea level pressure column from NOAA df.
        noaa_df = noaa_df.drop(columns=['Sea_Level_Pressure'])

        # Convert wind speed in NOAA df to m/s.
        noaa_df['Wind_Speed'] = noaa_df['Wind_Speed'] / 10

        # Change year to the AMY value
        for i, val in enumerate(Y):
             Y[i] = year

        # Change the dry bulb temperature to the AMY values.
        Tdb_new = noaa_df['Air_Temperature'].array
        for i, val in enumerate(Tdb):
            Tdb[i] = Tdb_new[i]

        # Change the dew point temperature to the AMY values.
        Tdew_new = noaa_df['Dew_Point_Temperature'].array
        for i, val in enumerate(Tdew):
            Tdew[i] = Tdew_new[i]

        # Change the pressure to the AMY values.
        Patm_new = noaa_df['Station_Pressure'].array
        for i, val in enumerate(Patm):
            Patm[i] = Patm_new[i]

        # Change the wind direction to the AMY values.
        Wdir_new = noaa_df['Wind_Direction'].array
        for i, val in enumerate(Wdir):
            Wdir[i] = Wdir_new[i]

        # Change the wind speed to the AMY values.
        Wspeed_new = noaa_df['Wind_Speed'].array
        for i, val in enumerate(Wspeed):
            Wspeed[i] = Wspeed_new[i]

        # Output information about any files that have values that will fail the EPW maximum/minimum criteria.
        # TODO: Write function to do these checks with a dictionary & append call
        if Tdb.min() < -70:
            epw_max_or_min_violations.loc[epw_counter, 'file'] = station_year
            epw_max_or_min_violations.loc[epw_counter, 'weather_variable'] = 'Tdb'
            epw_max_or_min_violations.loc[epw_counter, 'max_or_min'] = 'min'
            epw_max_or_min_violations.loc[epw_counter, 'limit_value'] = -70
            epw_max_or_min_violations.loc[epw_counter, 'extreme_observed_value'] = Tdb.min()
            epw_counter += 1
        if Tdb.max() > 70:
            epw_max_or_min_violations.loc[epw_counter, 'file'] = station_year
            epw_max_or_min_violations.loc[epw_counter, 'weather_variable'] = 'Tdb'
            epw_max_or_min_violations.loc[epw_counter, 'max_or_min'] = 'max'
            epw_max_or_min_violations.loc[epw_counter, 'limit_value'] = 70
            epw_max_or_min_violations.loc[epw_counter, 'extreme_observed_value'] = Tdb.max()
            epw_counter += 1
        if Tdew.min() < -70:
            epw_max_or_min_violations.loc[epw_counter, 'file'] = station_year
            epw_max_or_min_violations.loc[epw_counter, 'weather_variable'] = 'Tdew'
            epw_max_or_min_violations.loc[epw_counter, 'max_or_min'] = 'min'
            epw_max_or_min_violations.loc[epw_counter, 'limit_value'] = -70
            epw_max_or_min_violations.loc[epw_counter, 'extreme_observed_value'] = Tdew.min()
            epw_counter += 1
        if Tdew.max() > 70:
            epw_max_or_min_violations.loc[epw_counter, 'file'] = station_year
            epw_max_or_min_violations.loc[epw_counter, 'weather_variable'] = 'Tdew'
            epw_max_or_min_violations.loc[epw_counter, 'max_or_min'] = 'max'
            epw_max_or_min_violations.loc[epw_counter, 'limit_value'] = 70
            epw_max_or_min_violations.loc[epw_counter, 'extreme_observed_value'] = Tdew.max()
            epw_counter += 1
        if Patm.min() < 31000:
            epw_max_or_min_violations.loc[epw_counter, 'file'] = station_year
            epw_max_or_min_violations.loc[epw_counter, 'weather_variable'] = 'Patm'
            epw_max_or_min_violations.loc[epw_counter, 'max_or_min'] = 'min'
            epw_max_or_min_violations.loc[epw_counter, 'limit_value'] = 31000
            epw_max_or_min_violations.loc[epw_counter, 'extreme_observed_value'] = Patm.min()
            epw_counter += 1
        if Patm.max() > 120000:
            epw_max_or_min_violations.loc[epw_counter, 'file'] = station_year
            epw_max_or_min_violations.loc[epw_counter, 'weather_variable'] = 'Patm'
            epw_max_or_min_violations.loc[epw_counter, 'max_or_min'] = 'max'
            epw_max_or_min_violations.loc[epw_counter, 'limit_value'] = 120000
            epw_max_or_min_violations.loc[epw_counter, 'extreme_observed_value'] = Patm.max()
            epw_counter += 1
        if Wspeed.min() < 0:
            epw_max_or_min_violations.loc[epw_counter, 'file'] = station_year
            epw_max_or_min_violations.loc[epw_counter, 'weather_variable'] = 'Wspeed'
            epw_max_or_min_violations.loc[epw_counter, 'max_or_min'] = 'min'
            epw_max_or_min_violations.loc[epw_counter, 'limit_value'] = 0
            epw_max_or_min_violations.loc[epw_counter, 'extreme_observed_value'] = Wspeed.min()
            epw_counter += 1
        if Wspeed.max() > 40:
            epw_max_or_min_violations.loc[epw_counter, 'file'] = station_year
            epw_max_or_min_violations.loc[epw_counter, 'weather_variable'] = 'Wspeed'
            epw_max_or_min_violations.loc[epw_counter, 'max_or_min'] = 'max'
            epw_max_or_min_violations.loc[epw_counter, 'limit_value'] = 40
            epw_max_or_min_violations.loc[epw_counter, 'extreme_observed_value'] = Wspeed.max()
            epw_counter += 1
        if Wdir.min() < 0:
            epw_max_or_min_violations.loc[epw_counter, 'file'] = station_year
            epw_max_or_min_violations.loc[epw_counter, 'weather_variable'] = 'Wdir'
            epw_max_or_min_violations.loc[epw_counter, 'max_or_min'] = 'min'
            epw_max_or_min_violations.loc[epw_counter, 'limit_value'] = 0
            epw_max_or_min_violations.loc[epw_counter, 'extreme_observed_value'] = Wdir.min()
            epw_counter += 1
        if Wdir.max() > 360:
            epw_max_or_min_violations.loc[epw_counter, 'file'] = station_year
            epw_max_or_min_violations.loc[epw_counter, 'weather_variable'] = 'Wdir'
            epw_max_or_min_violations.loc[epw_counter, 'max_or_min'] = 'max'
            epw_max_or_min_violations.loc[epw_counter, 'limit_value'] = 360
            epw_max_or_min_violations.loc[epw_counter, 'extreme_observed_value'] = Wdir.max()
            epw_counter += 1

        # Grab the correct day of week to be written to the epw file
        day_dict = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
        day1 = pd.Series(noaa_df.first_valid_index())
        day_number = day1.dt.dayofweek[0]
        day_name = day_dict[day_number]

        # Write new EPW file.
        write_epw(amy_epw_file_out_path)

    except Exception as e:
        # Do the following if unable to complete the above process and convert to CSV.
        # TODO add in something to return the error
        no_epw.loc[no_counter, 'file'] = station_year
        no_counter += 1
        print('Problem processing: ' + station_year + ': ' + str(e))

# Write CSV of any NOAA files that were not processed into an EPW file.
if not no_epw.empty:
    no_epw.to_csv(create_out_path + '/no_epw_created.csv', index=False)
else:
    print('All files were converted to EPWs.')

# Write CSV of any files that have values that will fail the EPW maximum/minimum criteria.
if not epw_max_or_min_violations.empty:
    epw_max_or_min_violations.to_csv(create_out_path + '/epw_max_or_min_violations.csv', index=False)
else:
    print('No files were found to have issues with EPW maximum or minimum values.')

print('All files are processed. See create_amy_files_output in this directory for any issues.')