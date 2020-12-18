import pandas as pd
import os
from typing import Iterable

def analyze_noaa_isd_lite_files(
        files: Iterable,
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
        file = os.path.abspath(file)

        # Read the file into a Pandas dataframe.
        df = pd.read_csv(file,
                         delim_whitespace=True,
                         header=None,
                         compression=compression,
                         names=["Year", "Month", "Day", "Hour", "Air_Temperature",
                                "Dew_Point_Temperature", "Sea_Level_Pressure", "Wind_Direction",
                                "Wind_Speed_Rate", "Sky_Condition_Total_Coverage_Code",
                                "Liquid_Precipitation_Depth_Dimension_1H", "Liquid_Precipitation_Depth_Dimension_6H"]
                         )

        # Take year-month-day-hour columns and convert to datetime stamps.
        df['obs_timestamps'] = pd.to_datetime(pd.DataFrame({'year': df['Year'],
                                                            'month': df['Month'],
                                                            'day': df['Day'],
                                                            'hour': df['Hour']}))

        # Remove unnecessary year, month, day, hour columns
        df = df.drop(columns=['Year', 'Month', 'Day', 'Hour'])

        rows_present = df.shape[0]
        file_description = {
            'file': file,
            'total_rows_missing': 8760 - rows_present, # TODO: 8760 will not be right for leap years, we need handling for that case
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

def _get_max_missing_rows_from_hourly_dataframe(df:pd.DataFrame, timestamp_col_name:str) ->int:
    """
    Given a DataFrame containing hourly timestamps over a year, determine the longest sequence of timestamps
    missing from that DataFrame.

    :param df:
    :param timestamp_col_name:
    :return:
    """
    # Create series of continuous timestamp values for that year
    # TODO: 8760 will not be right for leap years, we need handling for that case
    all_timestamps = pd.date_range(df[timestamp_col_name].iloc[0], periods=8760, freq='H')

    # Merge to one dataframe containing all continuous timestamp values.
    all_times = pd.DataFrame(all_timestamps, columns=['all_timestamps'])
    df_all_times = pd.merge(all_times, df, how='left', left_on='all_timestamps', right_on=timestamp_col_name)

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
        if step == pd.Timedelta('1h'):
            counter += 1
            if counter > max_missing_rows:
                max_missing_rows = counter
        elif step > pd.Timedelta('1h'):
            counter = 1

    return max_missing_rows

