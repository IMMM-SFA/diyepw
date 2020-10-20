import os
import glob
import numpy as np
import pandas as pd
import argparse
import diyepw

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


def split_list_into_contiguous_segments(l:list, step):
    """
    Given a list, will return a new list of lists, where each of the inner lists is one block of contiguous
    values from the original list.

    Example: split_list_into_contiguous_segments([1, 2, 5, 6, 7, 9, 11], 1) =>
    [
        [1, 2],
        [5, 6, 7],
        [9],
        [11]
    ]

    :param l: The list to split. The values in this list must be of the same type as step_size, and must
      be of a type allowing sorting, as well as addition, such that you would expect some list item added to
      step_size to produce another valid list value. If the list contains duplicate entries, the duplicates
      will be removed.
    :param step: Items in the list that differ from one another by this amount will be considered
      neighbors in a contiguous segment.
    :return:
    """

    # Ensure the list is sorted and remove any duplicates
    l = list(set(l))
    l.sort()

    segments = []
    cur_segment = []
    prev_val = None
    for val in l:
        if prev_val is not None and val - step != prev_val:
            segments.append(cur_segment)
            cur_segment = [val]
        else:
            cur_segment.append(val)
        prev_val = val
    if len(cur_segment) > 0:
        segments.append(cur_segment)

    return segments

def handle_missing_values(
        df:pd.DataFrame, *, step, max_to_interpolate:int, max_to_impute:int,
        imputation_range, imputation_step, missing_values:list=[np.nan]
):
    """
    Look for missing values in a DataFrame. If possible, the missing values will be
    populated in place, using one of two strategies:

    If the missing values are in a contiguous block up to the length defined by max_to_interpolate,
    the values will linearly interpolated using the previous and following values.

    Otherwise, if the missing values are in a contiguous block up to the length defined by
    max_to_impute, the values will be imputed by going back through the indices by
    imputation_range, then stepping through by step sizes defined by imputation_step
    until the index that is imputation_range ahead of the missing value is found, and
    averaging all values encountered. For example, assuming a dataframe indexed by timestamp,
    if imputation_range is two weeks and imputation_step is 24 hours, a missing value will
    be imputed by calculating the average value at the same time of day every day going back
    two weeks and forward two weeks from the missing row.

    Otherwise, if the DataFrame contains at least one contiguous block of missing values
    larger than max_to_impute, it will be left unchanged, and an Exception will be raised.

    :param df: The dataframe to be searched for missing values.
    :param step: The step size to use in considering whether the indexes of the dataframe are
      contiguous. If two indices are one step apart, they are neighbors in a contiguous block.
      Otherwise they do not belong to the same contiguous block.
    :param max_to_interpolate: The maximum length of contiguous block to treat with the
      interpolation strategy described above.
    :param max_to_impute: The maximum length of contiguous block to treat with the imputation
      strategy described above.
    :param imputation_range: The distance before and after a missing record that will be searched
      for values to average when imputing a missing value
    :param imputation_step: The step-size to use in finding values to impute from, as described
      in the imputation strategy above.
    :param missing_values: Values matching any value in this list will be treated as missing.
    :return:
    """

    def get_indices_to_replace(df, col_name):
        indices_to_replace = df.index[df[col_name].isna()].tolist()
        indices_to_replace = split_list_into_contiguous_segments(
            indices_to_replace,
            step=step
        )
        return indices_to_replace

    # For simplicity's sake, set all missing values to NAN up front
    for col_name in df:
        df[col_name][df[col_name].isin(missing_values)] = np.nan

    for col_name in df:
        indices_to_replace = get_indices_to_replace(df, col_name)

        # There is no work to be done on this column if it has no missing data
        if len(indices_to_replace) == 0:
            continue

        # max(..., key=len) gives us the longest sequence, then we use len() to get that sequence's length
        max_sequence_length = len(max(indices_to_replace, key=len))

        # We raise an exception if a column has too many sequential missing rows; it's up to the calling
        # code to decide how we are going to handle records that can't be processed for this reason.
        if max_sequence_length > args.max_records_to_impute:
            # TODO: Add information about these files to outputs/create_amy_epw_files/no_epw_created.csv
            raise Exception("The longest set of missing records for {} is {}, but the max allowed is {}".format(
                col_name, max_sequence_length, max_to_impute
            ))

        # We make two passes to fill in missing records: The first pass uses the imputation strategy described
        # in this function's doc comment to fill in any gaps that are larger than max_to_interpolate. That
        # pass leaves behind any sequences that are smaller than that limit, and also leaves behind the first
        # and last item in any imputed sequence, which are also interpolated (i.e. set to the average of the imputed
        # value and the observed value on either side) to smooth out the transition between computed and observed
        # values.
        for indices in indices_to_replace:
            # Any blocks within our interpolation limit are skipped - they'll be filled in by the interpolate()
            # call below
            if len(indices) <= max_to_interpolate:
                continue

            # We will perform imputation on all the elements in the chunk *except* for the first and last
            # ones, which will be interpolated to smooth out the transition between computed and observed values
            indices_to_impute = indices[1:-1]

            # Set each missing value to the average of all the values in the range extending from imputation_range
            # indices behind to imputation_range indices ahead, walking through that range in steps whose size are
            # set by imputation_step.
            for index_to_impute in indices_to_impute:
                replacement_value_index = index_to_impute - imputation_range
                replacement_values = []
                while replacement_value_index <= index_to_impute + imputation_range:
                    if replacement_value_index in df.index:
                        replacement_values.append(df[col_name][replacement_value_index])
                    replacement_value_index += imputation_step

                # Take the mean of the values pulled. Will ignore NaNs.
                df[col_name][index_to_impute] = pd.Series(replacement_values, dtype=np.float64).mean()

    # Perform interpolation on any remaining missing values. At this point we know that there are no
    # sequences larger than the max permitted for interpolation, because they would have been imputed
    # or caused an exception (if larger than the imputation limit), so we can just call interpolate()
    # on anything that is still missing.
    df.interpolate(inplace=True)

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
                    help="""The maximum number of consecutive records to interpolate. See the documentation of the
                            pandas.DataFrame.interpolate() method's "limit" argument for more details. Basically,
                            if fields are missing, those missing values will be set to a value interpolated linearly
                            using the values of the fields immediately preceding and following the missing field(s).
                            If a sequence of fields longer than this argument is encountered, only this maximum number
                            of values will be interpolated, and the remaining set of missing fields will be imputed
                            by averaging the ."""
                    )

parser.add_argument('--max-records-to-impute',
                    default=48,
                    type=int,
                    help="""The maximum number of records to impute. For groups of missing records larger than the
                            limit set by --max-records-to-interpolate, we replace the missing values using the
                            average of the values two weeks prior and two weeks after the missing value. However, if
                            there are more missing records after interpolation than this limit (i.e. if a group of
                            missing records is larger than --max-records-to-interpolate PLUS --max-records-to-impute)
                            then the file will be discarded. Information about discarded files can be found in
                            outputs/create_amy_epw_files/no_epw_created.csv""")
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
        tmy = diyepw.TypicalMeteorologicalYear.from_tmy3_file(tmy3_epw_file_path)

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

        handle_missing_values(
            noaa_df,
            step=pd.Timedelta("1h"),
            max_to_interpolate=args.max_records_to_interpolate,
            max_to_impute=args.max_records_to_impute,
            imputation_range=pd.Timedelta("2w"),
            imputation_step=pd.Timedelta("1d"),
            missing_values=[np.nan, -9999.]
        )

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