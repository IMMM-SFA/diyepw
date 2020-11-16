import pandas as _pd
import os as _os
import tempfile as _tempfile
import math as _math
import numpy as _np
from glob import glob as _glob
from typing import Callable as _Callable
from typing import Iterable as _Iterable
from diyepw.meteorology import Meteorology

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
            amy_df = _clean_noaa_df(amy_df)

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
            amy_df_s = _clean_noaa_df(amy_df_s)

            # Grab the appropriate number of time steps for the subsequent year.
            amy_df_s = amy_df_s.head(abs_time_steps)

            # Append the NOAA dataframe for the subsequent year to the dataframe for the year of interest.
            amy_df = amy_df.append(amy_df_s)

            # Shift the timestamp (index) to match the time zone of the WMO station.
            amy_df = amy_df.shift(periods=tz_shift, freq='H')

            # Remove time steps that aren't applicable to the year of interest
            amy_df = amy_df[amy_df.index >= start_timestamp]

            _handle_missing_values(
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
                stp = _convert_sea_level_pressure_to_station_pressure(amy_df['Sea_Level_Pressure'][index], tmy.elevation)
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
