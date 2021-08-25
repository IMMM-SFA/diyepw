import pandas as pd


def analyze_noaa_isd_lite_file(
        file: str,
        compression: str = 'infer'
):
    """
    Performs an analysis of a single NOAA ISD Lite file, determining whether it is suitable for conversion into an AMY
    EPW file.

    :param file: The path of the NOAA ISD Lite file to be analyzed. The file may be uncompressed, or in any
       compression format permitted by pandas.read_csv(). If it is compressed, it must have a corresponding file
       extension, or the compression parameter must be passed. File name must begin with the WMO index of the
       weather station at which the observations in the file were recorded.
    :param compression: If you pass compressed files that don't end in the typical extension for their
       compression type (e.g. ".gz" for GZIP, ".zip" for ZIP, etc.) then you must pass this to indicate
       what the files' compression format is. See the documentation of the `compression` parameter of
       pandas.read_csv() for more information.

    :return: dict in the form:
        {
          'file': <str> - absolute path to the file,
          'total_rows_missing': <int> - The number of total rows that are missing data in this file,
          'max_consec_rows_missing': <int> - The largest number of consecutive rows that are missing data in this file
        }
    """
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
        'total_rows_missing': 8760 - rows_present,
        'max_consec_rows_missing': 0
    }
    # Skip the work of counting consecutive missing rows for files that have no missing rows
    if file_description['total_rows_missing'] > 0:
        file_description['max_consec_rows_missing'] = _get_max_missing_rows_from_hourly_dataframe(df, 'obs_timestamps')

    return file_description


def _get_max_missing_rows_from_hourly_dataframe(df: pd.DataFrame, timestamp_col_name: str) -> int:
    """
    Given a DataFrame containing hourly timestamps over a year, determine the longest sequence of timestamps
    missing from that DataFrame.

    :param df: The DataFrame from which to retrieve the maximum number of missing timestamps.
    :param timestamp_col_name: The name of the column containing timestamps in the DataFrame `df`
    :return: The size of the longest sequence of missing timestamps from the Dataframe `df`
    """
    # Create series of continuous timestamp values for that year
    all_timestamps = pd.date_range(df[timestamp_col_name].iloc[0], periods=8760, freq='H')

    # Merge to one dataframe containing all continuous timestamp values.
    all_times = pd.DataFrame(all_timestamps, columns=['all_timestamps'])
    df_all_times = pd.merge(all_times, df, how='left', left_on='all_timestamps', right_on=timestamp_col_name)

    # Create series of only the missing timestamp values
    missing_times = df_all_times[df_all_times.isnull().any(axis=1)]
    missing_times = missing_times['all_timestamps']

    if missing_times.empty: # pragma: no cover - This check is good defensive programming, but in practice we don't
        return 0            # actually call this function at all if the number of missing rows is 0

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

