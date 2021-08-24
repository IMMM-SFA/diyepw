import pandas as pd
import os
from typing import List, Tuple
from .create_amy_epw_file import create_amy_epw_file, _tempdir_amy_epw
from ._logging import _logger

def create_amy_epw_files_for_years_and_wmos(
        years: List[int],
        wmo_indices: List[int],

        *,
        max_records_to_interpolate: int = 6,
        max_records_to_impute: int = 48,
        max_missing_amy_rows: int = 700,
        amy_epw_dir: str = None,
        tmy_epw_dir: str = None,
        amy_dir: str = None,
        amy_files: Tuple[str, str] = None,
        allow_downloads: bool = False
) -> dict:
    """
    Create AMY EPW files for every combination of a set of WMO indices and years.

    Except for "years" and "wmos" being lists rather than single values, all parameters are identical in effect to
    create_amy_epw_file() - see that function's documentation for details.
    :param wmo_indices: A list of the WMO Indices of the weather stations for which the EPW files should be generated.
        Currently only weather stations in the United States are supported.
    :param years: A list of years for which the EPW files should be generated
    :param max_records_to_interpolate: The maximum length of sequence for which linear interpolation will be
        used to replace missing values. See the documentation of _handle_missing_values() below for details.
    :param max_records_to_impute: The maximum length of sequence for which imputation will be used to replace
        missing values. See the documentation of _handle_missing_values() below for details.
    :param max_missing_amy_rows: The maximum total number of missing rows to permit in a year's AMY file.
    :param amy_epw_dir: The directory into which the generated AMY EPW file should be written.
        If not defined, a temporary directory will be created. Note that, in addition to the generated AMY EPW files, an errors.csv file will be created in this
        directory if any errors were encountered, with error messages explaining which year/WMO Index combinations
        failed and why.
    :param tmy_epw_dir: The source directory for TMY EPW files. If a file for the requested WMO Index is
        already present, it will be used. Otherwise a TMY EPW file will be downloaded (see this package's
        get_tmy_epw_file() function for details). If no directory is given, the package's default
        directory (in data/tmy_epw_files/ in the package's directory) will be used, which will allow AMY
        files to be reused for future calls instead of downloading them repeatedly, which is quite time
        consuming.
    :param amy_dir: The source directory for AMY files. If a file for the requested WMO Index and year
        is already present, it will be used. Otherwise a TMY EPW file will be downloaded (see this package's
        get_noaa_isd_lite_file() function for details). If no directory is given, the package's default
        directory (in data/ in the package's directory) will be used, which will allow AMY files to be
        reused for future calls instead of downloading them repeatedly, which is quite time consuming.
    :param amy_files: Instead of specifying amy_dir and allowing this method to try to find the appropriate
        file, you can use this argument to specify the actual files that should be used. There should be
        two files - the first the AMY file for "year", and the second the AMY file for the subsequent year,
        which is required to support shifting the timezone from GMT to the timezone of the observed meteorology.
    :param allow_downloads: If this is set to True, then any missing TMY or AMY files required to generate the
        requested AMY EPW file will be downloaded from publicly available online catalogs. Otherwise, those files
        being missing will result in an error being raised.
    :return: A dictionary of the files generated for each year/wmo combination, in the form {
        <year>: {
            <wmo_index>: [<file_path>, ...],
            ...
        },
        ...
    }
    """
    amy_epw_files = {}

    # Initialize the df to hold information about year/WMO Index combinations for which no EPW could be generated
    errors = pd.DataFrame(columns=['year', 'wmo_index', 'error'])
    errors_path = os.path.join(amy_epw_dir if amy_epw_dir else _tempdir_amy_epw, "errors.csv")

    for year in years:
        for wmo_index in wmo_indices:
            _logger.info(f"Creating AMY EPW for year {year} and WMO {wmo_index}...")

            if not year in amy_epw_files:
                amy_epw_files[year] = {}
            if not wmo_index in amy_epw_files[year]:
                amy_epw_files[year][wmo_index] = []

            try:
                amy_epw_file = create_amy_epw_file(
                    wmo_index,
                    year,
                    max_records_to_interpolate=max_records_to_interpolate,
                    max_records_to_impute=max_records_to_impute,
                    max_missing_amy_rows=max_missing_amy_rows,
                    amy_epw_dir=amy_epw_dir,
                    tmy_epw_dir=tmy_epw_dir,
                    amy_dir=amy_dir,
                    amy_files=amy_files,
                    allow_downloads=allow_downloads
                )
                amy_epw_files[year][wmo_index].append(amy_epw_file)
            except Exception as e:
                errors = errors.append({"year": year, "wmo_index": wmo_index, "error": str(e)}, ignore_index=True)
                print(f'Problem processing year {year} and WMO index {wmo_index}: ' + str(e))

    if not errors.empty:
        _logger.warning(f"AMY EPW files could not be generated for {len(errors)} year/WMO Index combinations - see {errors_path} for more information")
        errors.to_csv(errors_path, mode='w', index=False)

    return amy_epw_files
