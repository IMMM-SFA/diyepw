import pandas as pd
import os
from typing import List, Optional, Tuple
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
        allow_downloads: bool = False,
        source: str = "auto",
        station_id: Optional[str] = None,
) -> dict:
    """
    Create AMY EPW files for every combination of a set of WMO indices and years.

    Except for ``years`` and ``wmo_indices`` being lists rather than single values, all parameters are
    identical in effect to :func:`create_amy_epw_file` - see that function's documentation for details.

    :param years: A list of years for which the EPW files should be generated.
    :param wmo_indices: A list of WMO Indices for which the EPW files should be generated.
    :param max_records_to_interpolate: The maximum length of sequence for which linear interpolation will
        be used to replace missing values.
    :param max_records_to_impute: The maximum length of sequence for which imputation will be used to
        replace missing values.
    :param max_missing_amy_rows: The maximum total number of missing rows to permit in a year's AMY file.
    :param amy_epw_dir: The directory into which the generated AMY EPW files should be written. If not
        defined, a temporary directory will be created. An ``errors.csv`` file is also written to this
        directory describing any year/WMO combinations that failed.
    :param tmy_epw_dir: The source directory for TMY EPW files.
    :param amy_dir: The source directory for AMY observation files (ISD-Lite or GHCNh).
    :param amy_files: A 2-tuple of (year_file, next_year_file). Only meaningful when ``wmo_indices`` and
        ``years`` each contain a single value, since the same explicit pair is reused per combination.
    :param allow_downloads: If True, any missing TMY or AMY files will be downloaded.
    :param source: Data source policy - ``"auto"``, ``"isd_lite"``, or ``"ghcnh"``. See
        :func:`create_amy_epw_file` for details.
    :param station_id: Optional GHCN station identifier for GHCNh access; defaults to the WMO->GHCN
        mapping shipped with diyepw.
    :return: A dictionary of the files generated for each year/wmo combination, in the form ``{
        <year>: { <wmo_index>: [<file_path>, ...] } }``.
    """
    amy_epw_files = {}

    # Initialize the df to hold information about year/WMO Index combinations for which no EPW could be generated
    errors = pd.DataFrame(columns=['year', 'wmo_index', 'error'])
    errors_path = os.path.join(amy_epw_dir if amy_epw_dir else _tempdir_amy_epw, "errors.csv")

    for year in years:
        for wmo_index in wmo_indices:
            _logger.info(f"Creating AMY EPW for year {year} and WMO {wmo_index}...")

            if year not in amy_epw_files:
                amy_epw_files[year] = {}
            if wmo_index not in amy_epw_files[year]:
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
                    allow_downloads=allow_downloads,
                    source=source,
                    station_id=station_id,
                )
                amy_epw_files[year][wmo_index].append(amy_epw_file)
            except Exception as e:
                errors = pd.concat(
                    [
                        errors,
                        pd.DataFrame(
                            [{"year": year, "wmo_index": wmo_index, "error": str(e)}]
                        ),
                    ],
                    ignore_index=True,
                )
                print(f'Problem processing year {year} and WMO index {wmo_index}: ' + str(e))

    if not errors.empty:
        _logger.warning(
            f"AMY EPW files could not be generated for {len(errors)} year/WMO Index combinations - "
            f"see {errors_path} for more information"
        )
        errors.to_csv(errors_path, mode='w', index=False)

    return amy_epw_files
