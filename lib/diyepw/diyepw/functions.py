import pandas as _pd
import numpy as _np
import os as _os
import math as _math
import tempfile as _tempfile
from collections.abc import Iterable as _Iterable
from typing import Callable as _Callable
from glob import glob as _glob
from .meteorology import Meteorology

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
    df['obs_timestamps'] = _pd.to_datetime(_pd.DataFrame({'year': df['Year'],
                                                        'month': df['Month'],
                                                        'day': df['Day'],
                                                        'hour': df['Hour']}))

    # Remove unnecessary year, month, day, hour columns and columns for variables not used to fill EPW.
    df = df.drop(columns=['Year', 'Month', 'Day', 'Hour', 'Sky_Condition_Total_Coverage_Code',
                          'Liquid_Precipitation_Depth_Dimension_1H', 'Liquid_Precipitation_Depth_Dimension_6H'])

    # Create series of continuous timestamp values for that year
    all_timestamps = _pd.date_range(df_year + '-01-01 00:00:00', df_year + '-12-31 23:00:00', freq='H')

    # Merge to one dataframe containing all continuous timestamp values.
    all_timestamps = _pd.DataFrame(all_timestamps, columns=['timestamp'])
    df = _pd.merge(all_timestamps, df, how='left', left_on='timestamp', right_on='obs_timestamps')
    df = df.drop(columns=['obs_timestamps'])

    # Set timestamps as index.
    df = df.set_index('timestamp')

    # Return the cleaned data frame.
    return df


####################################################################################################################
# Convert sea level pressure from NOAA ISD Lite data to station pressure
####################################################################################################################

def convert_sea_level_pressure_to_station_pressure(Pa, h_m) -> object:
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
        df:_pd.DataFrame, *, step, max_to_interpolate:int, max_to_impute:int,
        imputation_range, imputation_step, missing_values:list=None
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
    :param missing_values: Values matching any value in this list will be treated as missing. If not
      passed, defaults to numpy.nan
    :return:
    """

    if missing_values is None:
        missing_values = [_np.nan]

    def get_indices_to_replace(df, col_name):
        indices_to_replace = df.index[df[col_name].isna()].tolist()
        indices_to_replace = split_list_into_contiguous_segments(
            indices_to_replace,
            step=step
        )
        return indices_to_replace

    # For simplicity's sake, set all missing values to NAN up front
    for col_name in df:
        df[col_name][df[col_name].isin(missing_values)] = _np.nan

    for col_name in df:
        indices_to_replace = get_indices_to_replace(df, col_name)

        # There is no work to be done on this column if it has no missing data
        if len(indices_to_replace) == 0:
            continue

        # max(..., key=len) gives us the longest sequence, then we use len() to get that sequence's length
        max_sequence_length = len(max(indices_to_replace, key=len))

        # We raise an exception if a column has too many sequential missing rows; it's up to the calling
        # code to decide how we are going to handle records that can't be processed for this reason.
        if max_sequence_length > max_to_impute:
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
                df[col_name][index_to_impute] = _pd.Series(replacement_values, dtype=_np.float64).mean()

    # Perform interpolation on any remaining missing values. At this point we know that there are no
    # sequences larger than the max permitted for interpolation, because they would have been imputed
    # or caused an exception (if larger than the imputation limit), so we can just call interpolate()
    # on anything that is still missing.
    df.interpolate(inplace=True)

def analyze_noaa_isd_lite_files(
        files: _Iterable,
        *,
        max_missing_rows: int,
        max_consecutive_missing_rows: int,
        compression:str='infer'
):
    """
    Performs an analysis of a set of NOAA ISD Lite files, determining which of them are suitable
    for conversion into AMY EPW files.

    :param files: An collection of paths to the NOAA ISD Lite files to be analyzed. The files may be
       uncompressed, or in any compression format permitted by pandas.read_csv(). If they are
       compressed, they need to have a corresponding file extension, or the compression parameter
       must be passed. File names must begin with the WMO index of the weather station at which the
       observations in the file were recorded.
    :param max_missing_rows: The maximum number of total missing rows to allow in a file.
    :param max_consecutive_missing_rows: The maximum number of consecutive missing rows to allow in a file.
    :param compression: If you pass compressed files that don't end in the typical extension for their
       compression type (e.g. ".gz" for GZIP, ".zip" for ZIP, etc.) then you must pass this to indicate
       what the files' compression format is. See the documentation of the `compression` parameter of
       pandas.read_csv() for more information.

    :return: dict in the form:
    {
      "good": [<file_description>, ...],
      "too_many_total_rows_missing": [<file_description>, ...],
      "too_many_consecutive_rows_missing": [<file_description>, ...]
    }
    ...where <file_description> is itself a dict in the form:
    {
      'file': <str> - absolute path to the file,
      'total_rows_missing': <int> - The number of total rows that are missing data in this file,
      'max_consec_rows_missing': <int> - The largest number of consecutive rows that are missing data in this file
    }
    """

    too_many_missing_rows = []
    too_many_consecutive_missing_rows = []
    good_files = []

    # Loop through all .gz files in the input directory - we filter on extension so that things like
    # README files can be in that path without causing any problems. We filter on files that begin
    # with 7 because all NOAA ISD Lite files for North America should start with 7, as all WMO indices
    # in North America do.
    for file in files:

        # It's nicer to work with absolute paths, especially since we are going to put this path in a
        # file to share with another script - otherwise that other script needs to know where this
        # script is located to make sense of the relative paths
        file = _os.path.abspath(file)

        # Read the file into a Pandas dataframe.
        df = _pd.read_csv(file,
                         delim_whitespace=True,
                         header=None,
                         compression=compression,
                         names=["Year", "Month", "Day", "Hour", "Air_Temperature",
                                "Dew_Point_Temperature", "Sea_Level_Pressure", "Wind_Direction",
                                "Wind_Speed_Rate", "Sky_Condition_Total_Coverage_Code",
                                "Liquid_Precipitation_Depth_Dimension_1H", "Liquid_Precipitation_Depth_Dimension_6H"]
                         )

        # Take year-month-day-hour columns and convert to datetime stamps.
        df['obs_timestamps'] = _pd.to_datetime(_pd.DataFrame({'year': df['Year'],
                                                            'month': df['Month'],
                                                            'day': df['Day'],
                                                            'hour': df['Hour']}))

        # Remove unnecessary year, month, day, hour columns
        df = df.drop(columns=['Year', 'Month', 'Day', 'Hour'])

        rows_present = df.shape[0]
        file_description = {
            'file': file,
            'total_rows_missing': 8760 - rows_present,
            'max_consec_rows_missing': 0
        }
        # Skip the work of counting consecutive missing rows for files that have no missing rows
        if file_description['total_rows_missing'] > 0:
            file_description['max_consec_rows_missing'] = _get_max_missing_rows_from_hourly_dataframe(df, 'obs_timestamps')

        # Depending on how many total and consecutive rows are missing, add the current file to one of our
        # collections to be returned to the caller
        if file_description['total_rows_missing'] > max_missing_rows:
            too_many_missing_rows.append(file_description)
        elif file_description['max_consec_rows_missing'] > max_consecutive_missing_rows:
            too_many_consecutive_missing_rows.append(file_description)
        else:
            good_files.append(file_description)

    return {
        "good": good_files,
        "too_many_total_rows_missing": too_many_missing_rows,
        "too_many_consecutive_rows_missing": too_many_consecutive_missing_rows
    }

def _get_max_missing_rows_from_hourly_dataframe(df:_pd.DataFrame, timestamp_col_name:str) ->int:
    """
    Given a DataFrame containing hourly timestamps over a year, determine the longest sequence of timestamps
    missing from that DataFrame.

    :param df:
    :param timestamp_col_name:
    :return:
    """
    # Create series of continuous timestamp values for that year
    all_timestamps = _pd.date_range(df[timestamp_col_name].iloc[0], periods=8760, freq='H')

    # Merge to one dataframe containing all continuous timestamp values.
    all_times = _pd.DataFrame(all_timestamps, columns=['all_timestamps'])
    df_all_times = _pd.merge(all_times, df, how='left', left_on='all_timestamps', right_on=timestamp_col_name)

    # Create series of only the missing timestamp values
    missing_times = df_all_times[df_all_times.isnull().any(axis=1)]
    missing_times = missing_times['all_timestamps']

    if missing_times.empty:
        return 0

    # Create a series containing the time step distance from the previous timestamp for the missing timestamp values
    missing_times_diff = missing_times.diff()

    # Count the maximum number of consecutive missing time steps.
    counter = 1
    max_missing_rows = 1
    for step in missing_times_diff:
        if step == _pd.Timedelta('1h'):
            counter += 1
            if counter > max_missing_rows:
                max_missing_rows = counter
        elif step > _pd.Timedelta('1h'):
            counter = 1

    return max_missing_rows

def convert_noaa_isd_lite_to_amy_epw_files(
        amy_file_paths:_Iterable,
        *,
        max_records_to_interpolate:int,
        max_records_to_impute:int,
        output_dir:str = None,
        progress_handler:_Callable[[str], None] = None
):
    """
    Given a set of NOAA ISD Lite files, will generate a corresponding set of EPW files by substituting observed values
    from the NOAA ISD Lite files into an EPW representing a typical meteorological year for the same WMO Index. For more
    details, see the main documentation of this project.
    :param amy_file_paths: A collection of paths to NOAA ISD Lite files that should be converted. File names must
        conform to the format "<WMO ID>-<...>-<YEAR>" and may have no extension (if they are in raw text format) or
        the appropriate extension for any of the compressed formats accepted by pandas.read_csv() if they are
        compressed.
    :param max_records_to_interpolate: The maximum number of consecutive records to interpolate. See the documentation
        of the pandas.DataFrame.interpolate() method's "limit" argument for more details. Basically, if a sequence of
        fields up to the length defined by this argument are missing, those missing values will be interpolated linearly
        using the values of the fields immediately preceding and following the missing field(s). If a sequence of fields
        is longer than this limit, then those fields' values will be imputed instead (see max_records_to_impute)
    :param max_records_to_impute: The maximum number of records to impute. For groups of missing records larger than the
                            limit set by --max-records-to-interpolate, we replace the missing values using the
                            average of the values two weeks prior and two weeks after the missing value. However, if
                            there are more missing records after interpolation than this limit (i.e. if a group of
                            missing records is larger than --max-records-to-interpolate PLUS --max-records-to-impute)
                            then the file will be discarded.
    :param output_dir: The directory into which the generated EPW files will be written. If not passed, the files will
        be written to a temporary location depending on the operating system the script is run in.
    :param progress_handler: An optional function that, if passed, will be invoked for each file and will be passed
        the file path about to be processed
    :return: A tuple consisting of:
        - A list of paths to all successfully generated EPW files
        - A Dataframe with the columns "file" and "error" describing all files that could not be generated due to errors
    """
    # Initialize the df to hold paths of AMY files that could not be converted to an EPW.
    errors = _pd.DataFrame(columns=['file', 'error'])

    # Initialize the list of paths of successfully generated EPW files
    amy_epw_file_paths = []

    # If no output directory was specified, create a temporary directory
    if output_dir is None:
        output_dir = _tempfile.mkdtemp()

    # Iterate through the set of AMY files, attempting to convert each one to an EPW file based on the
    # corresponding TMY file
    for amy_file_path in amy_file_paths:
        if progress_handler is not None:
            progress_handler(amy_file_path)

        try:
            amy_file_name = _os.path.basename(amy_file_path)
            amy_file_name_without_ext = _os.path.splitext(amy_file_name)[0]

            # Get the station number and year from the AMY file name
            wmo_station_id = amy_file_name_without_ext.split("-")[0]
            year = int(amy_file_name_without_ext.split("-")[-1])

            # Get path to the TMY EPW file corresponding to that station.
            tmy3_epw_file_path = _glob(
                _os.path.join('..', 'inputs', 'Energy_Plus_TMY3_EPW', f'*.{wmo_station_id}_TMY3.epw')
            )[0]

            # Read in the NOAA AMY file for the station
            amy_df = _pd.read_csv(amy_file_path, delim_whitespace=True, header=None)
            amy_df = clean_noaa_df(amy_df)

            # Save the first timestamp for that year; we will need it later after we time-shift so that we can trim
            # the data to only values after this time
            start_timestamp = amy_df.index[0]

            # Read in the corresponding TMY3 EPW file.
            tmy = Meteorology.from_tmy3_file(tmy3_epw_file_path)

            # Identify the time zone shift as an integer.
            tz_shift = tmy.timezone_gmt_offset

            # Identify the number of time steps to be obtained from the subsequent year's NOAA file.
            abs_time_steps = _math.ceil(abs(tz_shift))

            # Identify the name of the subsequent year's NOAA file.
            # TODO: This is still dependent on a specific path. We need to rewrite the function such that we aren't
            #     passing complete file paths at all, but instead indicate a directory in which NOAA ISD Lite files
            #     are to be searched for, then pass a collection of years and WMOs. That will make this path
            #     specification unnecessary, and takes us one step closer to offering generic functionality to generate
            #     AMY EPW files for arbitrary year/WMO combinations
            year_s_string = str(int(year) + 1)
            glob_string = _os.path.abspath(
                _os.path.join('..', 'inputs', 'NOAA_ISD_Lite_Raw', '**', wmo_station_id + '*' + year_s_string + '*')
            )
            noaa_amy_s_info_path = _glob(glob_string)
            if len(noaa_amy_s_info_path) == 0:
                raise Exception("Couldn't load subsequent year's data: no file was found matching '" + glob_string + "'")
            noaa_amy_s_info_path = noaa_amy_s_info_path[0]

            # Read in the NOAA AMY file for the station for the subsequent year.
            amy_df_s = _pd.read_csv(noaa_amy_s_info_path,
                                   delim_whitespace=True,
                                   header=None)

            # Clean the NOAA AMY data frame for the subsequent year.
            # TODO: Can't we join the DFs together first and then do the cleanup so there's only one cleanup call? Also
            #    that would preclude us from cleaning up a lot of data that we're going to immediately discard in any
            #    case
            amy_df_s = clean_noaa_df(amy_df_s)

            # Grab the appropriate number of time steps for the subsequent year.
            amy_df_s = amy_df_s.head(abs_time_steps)

            # Append the NOAA dataframe for the subsequent year to the dataframe for the year of interest.
            amy_df = amy_df.append(amy_df_s)

            # Shift the timestamp (index) to match the time zone of the WMO station.
            amy_df = amy_df.shift(periods=tz_shift, freq='H')

            # Remove time steps that aren't applicable to the year of interest
            amy_df = amy_df[amy_df.index >= start_timestamp]

            handle_missing_values(
                amy_df,
                step=_pd.Timedelta("1h"),
                max_to_interpolate=max_records_to_interpolate,
                max_to_impute=max_records_to_impute,
                imputation_range=_pd.Timedelta("2w"),
                imputation_step=_pd.Timedelta("1d"),
                missing_values=[_np.nan, -9999.]
            )

            # Initialize new column for station pressure (not strictly necessary)
            amy_df['Station_Pressure'] = None

            # Convert sea level pressure in NOAA df to atmospheric station pressure in Pa.
            for index in amy_df.index:
                stp = convert_sea_level_pressure_to_station_pressure(amy_df['Sea_Level_Pressure'][index], tmy.elevation)
                amy_df.loc[index, 'Station_Pressure'] = stp

            # Change observation values to the values taken from the AMY data
            tmy.set('year', year)
            tmy.set('Tdb', [i / 10 for i in amy_df['Air_Temperature']]) # Convert AMY value to degrees C
            tmy.set('Tdew', [i / 10 for i in amy_df['Dew_Point_Temperature']]) # Convert AMY value to degrees C
            tmy.set('Patm', amy_df['Station_Pressure'])
            tmy.set('Wdir', amy_df['Wind_Direction'])
            tmy.set('Wspeed', [i / 10 for i in amy_df['Wind_Speed']]) # Convert AMY value to m/sec

            # Check for violations of EPW file standards
            epw_rule_violations = tmy.validate_against_epw_rules()
            if len(epw_rule_violations) > 0:
                raise Exception("EPW validation failed:\n" + "\n".join(epw_rule_violations))

            # Write new EPW file if no validation errors were found.
            amy_epw_file_name = f"{tmy.country}_{tmy.state}_{tmy.city}.{tmy.station_number}_AMY_{year}.epw"
            amy_epw_file_name = amy_epw_file_name.replace(" ", "-")
            amy_epw_file_path = _os.path.join(output_dir, amy_epw_file_name)
            tmy.write_epw(amy_epw_file_path)
            amy_epw_file_paths.append(amy_epw_file_path)

        except Exception as e:
            errors = errors.append({"file": amy_file_path, "error": str(e)}, ignore_index=True)
            print('Problem processing ' + amy_file_path + ': ' + str(e))

    return amy_epw_file_paths, errors

def get_wmo_station_location(wmo_station_number:int):
    """
        Get the state, and county associated with a WMO station
        :param wmo_station_number: The WMO Station ID of the weather station to get location information for
        :return: Either a dict with fields "state" and "county", or None if no information is available for
            the passed WMO Station ID
    """


    wmo_station_info_filepath = _os.path.join('..', 'inputs', 'Weather_Stations_by_County.csv')

    if not _os.path.exists(wmo_station_info_filepath):
        raise Exception("Missing WMO station info file at " + wmo_station_info_filepath)

    wmo_station_info = _pd.read_csv(wmo_station_info_filepath)

    station_of_interest = wmo_station_info[wmo_station_info['Station WMO Identifier'] == wmo_station_number]

    if len(station_of_interest.index) == 0:
        return None

    station_of_interest = station_of_interest.iloc[0]

    return {
        "state": station_of_interest.State,
        "county": station_of_interest.County
    }
