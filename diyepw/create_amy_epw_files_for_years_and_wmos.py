import pandas as pd
import os
from typing import List, Tuple
from .create_amy_epw_file import create_amy_epw_file, _tempdir_amy_epw
from ._logging import _logger

def create_amy_epw_files_for_years_and_wmos(
        years: List[int],
        wmo_indices: List[int],

        *,
        max_records_to_interpolate: int,
        max_records_to_impute: int,
        max_missing_amy_rows: int,
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
    :param wmo_indices:
    :param years:
    :param max_records_to_interpolate:
    :param max_records_to_impute:
    :param max_missing_amy_rows:
    :param amy_epw_dir: Note that, in addition to the generated AMY EPW files, an errors.csv file will be created in this
        directory if any errors were encountered, with error messages explaining which year/WMO Index combinations
        failed and why.
    :param tmy_epw_dir:
    :param amy_dir:
    :param amy_files:
    :param allow_downloads:
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
