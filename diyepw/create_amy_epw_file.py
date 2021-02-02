from .get_tmy_epw_file import get_tmy_epw_file
from .get_noaa_isd_lite_file import get_noaa_isd_lite_file
from .meteorology import Meteorology
from .analyze_noaa_isd_lite_file import analyze_noaa_isd_lite_file

import tempfile
import pandas as pd
import numpy as np
import os
import pkg_resources
from typing import Tuple

from ._logging import _logger

# We buffer this path so that we don't create tons of temporary directories if the function is called many
# times, and so that calling it multiple times with the same WMO/year combination won't result in the same
# file being generated multiple times.
_tempdir_amy_epw = tempfile.mkdtemp()

def create_amy_epw_file(
        wmo_index:int,
        year:int,

        *,
        max_records_to_interpolate:int,
        max_records_to_impute:int,
        max_missing_amy_rows:int = None,
        amy_epw_output_dir:str = None,
        tmy_epw_input_dir:str = None,
        amy_input_dir:str = None,
        amy_input_files:Tuple[str, str] = None,
        allow_downloads:bool = False,
        file_type:str = "tmy3"
) -> str:
    """
    Combine data from a Typical Meteorological Year (TMY) EPW file and Actual Meteorological Year (AMY)
    observed data to generate an AMY EPW file for a single calendar year at a given WMO.
    :param wmo_index: The WMO Index of the weather station for which the EPW file should be generated.
        Currently only weather stations in the United States are supported.
    :param year: The year for which the EPW should be generated
    :param amy_epw_output_dir: The directory into which the generated AMY EPW file should be written.
        If not defined, a temporary directory will be created
    :param tmy_epw_input_dir: The source directory for TMY EPW files. If a file for the requested WMO Index is
        already present, it will be used. Otherwise a TMY EPW file will be downloaded (see this package's
        get_tmy_epw_file() function for details). If no directory is given, the package's default
        directory (in data/tmy_epw_files/ in the package's directory) will be used, which will allow AMY
        files to be reused for future calls instead of downloading them repeatedly, which is quite time
        consuming.
    :param amy_input_dir: The source directory for AMY files. If a file for the requested WMO Index and year
        is already present, it will be used. Otherwise a TMY EPW file will be downloaded (see this package's
        get_noaa_isd_lite_file() function for details). If no directory is given, the package's default
        directory (in data/ in the package's directory) will be used, which will allow AMY files to be
        reused for future calls instead of downloading them repeatedly, which is quite time consuming.
    :param amy_input_files: Instead of specifying amy_dir and allowing this method to try to find the appropriate
        file, you can use this argument to specify the actual files that should be used. There should be
        two files - the first the AMY file for "year", and the second the AMY file for the subsequent year,
        which is required to support shifting the timezone from GMT to the timezone of the observed meteorology.
    :param max_records_to_interpolate: The maximum length of sequence for which linear interpolation will be
        used to replace missing values. See the documentation of _handle_missing_values() below for details.
    :param max_records_to_impute: The maximum length of sequence for which imputation will be used to replace
        missing values. See the documentation of _handle_missing_values() below for details.
    :param max_missing_amy_rows: The maximum total number of missing rows to permit in a year's AMY file.
    :param allow_downloads: If this is set to True, then any missing TMY or AMY files required to generate the
        requested AMY EPW file will be downloaded from publicly available online catalogs. Otherwise, those files
        being missing will result in an error being raised.
    :param file_type: The format of the AMY files. Either "wrf_netcdf" or "tmy3". If this is "wrf_netcdf", then the
        files must be present in amy_input_dir, or the files must be explicitly set using amy_files, because there is
        no handling for automatic downloads of WRF NetCDF files.
    :return: The absolute path of the generated AMY EPW file
    """

    if amy_input_dir is not None and amy_input_files is not None:
        raise Exception("It is not possible to specify both amy_dir and amy_files")
    if file_type == 'wrf_netcdf' and allow_downloads is True:
        raise Exception(
            "If file_type is 'wrf_netcdf', you cannot pass allow_downloads=True, because the DIYEPW package cannot "
            "automatically download wrf_netcdf files from an online repository"
        )

    if amy_epw_output_dir is None:
        global _tempdir_amy_epw
        amy_epw_output_dir = _tempdir_amy_epw
        _logger.debug(f"No amy_epw_dir was specified - generated AMY EPWs will be stored in {amy_epw_output_dir}")

    # Either amy_files is specified, in which case we use the specified paths, or amy_dir is specified,
    # in which case we will search that directory for AMY files, or neither is specified, in which case
    # we will fall back to a generated temporary directory.
    if amy_input_files is not None:
        for p in amy_input_files:
            if not os.path.exists(p):
                raise Exception(f'Path {p} does not exist')

        amy_input_file_path, amy_input_next_year_file_path = amy_input_files
    else:
        if amy_input_dir is None:
            amy_input_dir = pkg_resources.resource_filename("diyepw", "data/noaa_isd_lite_files")
            _logger.debug(f"No amy_dir was specified - downloaded AMY files will be stored in the default location at {amy_input_dir}")

        amy_input_file_path = get_noaa_isd_lite_file(wmo_index, year, output_dir=amy_input_dir, allow_downloads=allow_downloads)
        amy_input_next_year_file_path = get_noaa_isd_lite_file(wmo_index, year + 1, output_dir=amy_input_dir, allow_downloads=allow_downloads)

    if max_missing_amy_rows is not None:
        amy_file_analysis = analyze_noaa_isd_lite_file(amy_input_file_path)
        if amy_file_analysis['total_rows_missing'] > max_missing_amy_rows:
            raise Exception(f"File is missing {amy_file_analysis['total_rows_missing']} rows, but maximum allowed is {max_missing_amy_rows}")

    # Read in the corresponding TMY3 EPW file.
    tmy_input_epw_file_path = get_tmy_epw_file(wmo_index, tmy_epw_input_dir, allow_downloads=allow_downloads)
    meteorology = Meteorology.from_tmy3_file(tmy_input_epw_file_path)

    amy_epw_output_file_name = f"{meteorology.country}_{meteorology.state}_{meteorology.city}.{meteorology.station_number}_AMY_{year}.epw"
    amy_epw_output_file_name = amy_epw_output_file_name.replace(" ", "-")
    amy_epw_output_file_path = os.path.join(amy_epw_output_dir, amy_epw_output_file_name)

    if os.path.exists(amy_epw_output_file_path):
        _logger.debug(f"File already exists at {amy_epw_output_file_path}, so a new one won't be generated.")
        return amy_epw_output_file_path

    amy_df = _get_amy_df(
        (amy_input_file_path, amy_input_next_year_file_path),
        meteorology.elevation,
        meteorology.timezone_gmt_offset,
        year,
        file_type
    )

    # TODO: analyze_noaa_isd_lite_file() needs to be rewritten to take the amy_df as an argument instead, so that
    # it can validate the dataframe regardless of what format the input files are in
    if max_missing_amy_rows is not None:
        amy_input_file_analysis = analyze_noaa_isd_lite_file(amy_input_file_path)
        if amy_input_file_analysis['total_rows_missing'] > max_missing_amy_rows:
            raise Exception(f"File is missing {amy_input_file_analysis['total_rows_missing']} rows, but maximum allowed is {max_missing_amy_rows}")

    _handle_missing_values(
        amy_df,
        step=pd.Timedelta("1h"),
        max_to_interpolate=max_records_to_interpolate,
        max_to_impute=max_records_to_impute,
        imputation_range=pd.Timedelta("2w"),
        imputation_step=pd.Timedelta("1d"),
        missing_values=[np.nan, -9999.]
    )

    # Change observation values to the values taken from the AMY data
    meteorology.set('year', year)
    meteorology.set('Tdb', [i / 10 for i in amy_df['Air_Temperature']])  # Convert AMY value to degrees C
    meteorology.set('Tdew', [i / 10 for i in amy_df['Dew_Point_Temperature']])  # Convert AMY value to degrees C
    meteorology.set('Patm', amy_df['Station_Pressure'])
    meteorology.set('Wdir', amy_df['Wind_Direction'])
    meteorology.set('Wspeed', [i / 10 for i in amy_df['Wind_Speed']])  # Convert AMY value to m/sec

    # Check for violations of EPW file standards
    epw_rule_violations = meteorology.validate_against_epw_rules()
    if len(epw_rule_violations) > 0:
        raise Exception("EPW validation failed:\n" + "\n".join(epw_rule_violations))

    # Write new EPW file if no validation errors were found.
    meteorology.write_epw(amy_epw_output_file_path)

    return amy_epw_output_file_path

def _get_amy_df(file_paths:Tuple[str, str], elevation:int, timezone_gmt_offset:int, year:int, file_type:str) -> pd.DataFrame:
    """
    Generate a DataFrame that contains a set of values to be substituted into a TMY EPW file in order to
    generate an AMY EPW file.

    :param file_paths: The paths to the AMY files to be opened. The first path must point to the AMY file for the year
        to be examined, and the second path to the AMY file for the subsequent year. This is necessary because we
        retrieve data from January 1 of the subsequent year to allow for time-zone shifting without leaving empty
        hours the evening of December 31.
    :param file_type: One of "wrf_netcdf" or "tmy3"
    :return: A DataFrame with the following fields:
    """
    if file_type == 'wrf_netcdf':
        return _get_amy_df_for_wrf_netcdf(file_paths)

    elif file_type == "tmy3":
        return _get_amy_df_for_tmy3_epw(file_paths, elevation, timezone_gmt_offset, year)

    raise Exception(f"Unexpected value, '{file_type}', of file_type")

def _get_amy_df_for_tmy3_epw(file_paths:Tuple[str, str], elevation:int, timezone_gmt_offset:int, year:int):
    # Read in the NOAA AMY file for the station for the requested year as well as the first 23 hours (sufficient
    # to handle the largest possible timezone shift) of the subsequent year - the subsequent year's data will be
    # used to populate the last hours of the year because of the time shift that we perform, which moves the first
    # hours of January 1 into the final hours of December 31.
    amy_df = pd.read_csv(file_paths[0], delim_whitespace=True, header=None)
    amy_next_year_df = pd.read_csv(file_paths[1], delim_whitespace=True, header=None, nrows=23)
    amy_df = pd.concat([amy_df, amy_next_year_df]).reset_index(drop=True)

    amy_df = _set_noaa_df_columns(amy_df)
    amy_df = _create_timestamp_index_for_noaa_df(amy_df)

    # Initialize new column for station pressure (not strictly necessary)
    amy_df['Station_Pressure'] = None

    # Convert sea level pressure in NOAA df to atmospheric station pressure in Pa.
    # -9999 represents a missing value, so rows with this value are not converted
    for index in amy_df[amy_df["Sea_Level_Pressure"] != -9999].index:
        stp = _convert_sea_level_pressure_to_station_pressure(amy_df['Sea_Level_Pressure'][index], elevation)
        amy_df.loc[index, 'Station_Pressure'] = stp

    # Shift the timestamp (index) to match the time zone of the WMO station.
    amy_df = amy_df.shift(periods=timezone_gmt_offset, freq='H')

    # Remove time steps that aren't applicable to the year of interest
    amy_df = _map_noaa_df_to_year(amy_df, year)

    return amy_df

def _get_amy_df_for_wrf_netcdf(filepaths:Tuple[str, str]):
    pass

def _set_noaa_df_columns(df:pd.DataFrame) -> pd.DataFrame:
    """Add headings to a NOAA ISD Lite formatted dataframe, and Drop columns for observations
    that won't be used in populating the EPW files.
    """
    list_of_columns = ["Year", "Month", "Day", "Hour", "Air_Temperature",
                       "Dew_Point_Temperature", "Sea_Level_Pressure", "Wind_Direction",
                       "Wind_Speed", "Sky_Condition_Total_Coverage_Code",
                       "Liquid_Precipitation_Depth_Dimension_1H", "Liquid_Precipitation_Depth_Dimension_6H"]
    df.columns = list_of_columns

    # Remove unnecessary columns
    df = df.drop(columns=[
        'Sky_Condition_Total_Coverage_Code',
        'Liquid_Precipitation_Depth_Dimension_1H',
        'Liquid_Precipitation_Depth_Dimension_6H'
    ])

    return df

def _create_timestamp_index_for_noaa_df(df:pd.DataFrame) -> pd.DataFrame:
    """Convert the year, month, day fields of a NOAA ISD Lite DataFrame into
    a timestamp and make that timestamp the index of the DataFrame
    :param df:
    :return:
    """
    df['timestamp'] = pd.to_datetime(pd.DataFrame({'year': df['Year'],
                                                   'month': df['Month'],
                                                   'day': df['Day'],
                                                   'hour': df['Hour']}))
    df = df.set_index('timestamp')

    # Remove unnecessary columns
    df = df.drop(columns=['Year', 'Month', 'Hour', 'Day'])

    return df

def _map_noaa_df_to_year(df, year):
    """Add headings to a NOAA ISD Lite formatted dataframe, convert year-month-day-hour columns to a timestamp,
    set the timestamp as index, and make sure each hour of the DF's range has a timestamp, regardless of whether
    there are any observations in that hour. Drop columns for observations that won't be used in populating the
    EPW files.

    The assumption of this function is that the dataframe ranges from the beginning of the year to some
    """
    # Create series of continuous timestamp values for that year
    all_timestamps = pd.date_range(str(year) + '-01-01 00:00:00', str(year) + '-12-31 23:00:00', freq='H')
    all_timestamps = pd.DataFrame(all_timestamps, columns=['timestamp'])

    # Merge to one dataframe containing all continuous timestamp values.
    df = pd.merge(all_timestamps, df, how='left', left_on='timestamp', right_index=True)
    df = df.set_index('timestamp')

    return df

def _handle_missing_values(
        df:pd.DataFrame, *, step, max_to_interpolate:int, max_to_impute:int,
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

    if missing_values is None: # pragma: no cover - We don't currently have any calls that don't specify this argument
        missing_values = [np.nan]

    def get_indices_to_replace(df, col_name):
        indices_to_replace = df.index[df[col_name].isna()].tolist()
        indices_to_replace = _split_list_into_contiguous_segments(
            indices_to_replace,
            step=step
        )
        return indices_to_replace

    # For simplicity's sake, set all missing values to NAN up front
    for col_name in df:
        df.loc[df[col_name].isin(missing_values), col_name] = np.nan

    for col_name in df:
        indices_to_replace = get_indices_to_replace(df, col_name)

        # There is no work to be done on this column if it has no missing data
        if len(indices_to_replace) == 0: # pragma: no cover
            continue

        # max(..., key=len) gives us the longest sequence, then we use len() to get that sequence's length
        max_sequence_length = len(max(indices_to_replace, key=len))

        # We raise an exception if a column has too many sequential missing rows; it's up to the calling
        # code to decide how we are going to handle records that can't be processed for this reason.
        if max_sequence_length > max_to_impute: # pragma: no cover - We check for this case before this function is called
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

def _split_list_into_contiguous_segments(l:list, step):
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

def _convert_sea_level_pressure_to_station_pressure(Pa, h_m) -> object:
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

    return Pstn