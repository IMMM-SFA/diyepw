import os
from typing import Iterable
from ._logging import _logger
from .analyze_noaa_isd_lite_file import analyze_noaa_isd_lite_file


def analyze_noaa_isd_lite_files(
        files: Iterable,
        *,
        max_missing_rows: int = 700,
        max_consecutive_missing_rows: int = 48,
        compression: str = 'infer'
):
    """
    Performs an analysis of a set of NOAA ISD Lite files, determining which of them are suitable
    for conversion into AMY EPW files.

    :param files: An collection of paths to the NOAA ISD Lite files to be analyzed. See this package's
        analyze_noaa_isd_lite_file() function for more information.
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

    for file in files:

        # It's nicer to work with absolute paths, especially since we are going to put this path in a
        # file to share with another script - otherwise that other script needs to know where this
        # script is located to make sense of the relative paths
        file = os.path.abspath(file)

        file_description = analyze_noaa_isd_lite_file(file, compression)

        # Depending on how many total and consecutive rows are missing, add the current file to one of our
        # collections to be returned to the caller
        if file_description['total_rows_missing'] > max_missing_rows:
            _logger.info(f"{file} has too many total missing rows")
            too_many_missing_rows.append(file_description)
        elif file_description['max_consec_rows_missing'] > max_consecutive_missing_rows:
            _logger.info(f"{file} has too many consecutive missing rows")
            too_many_consecutive_missing_rows.append(file_description)
        else:
            _logger.info(f"{file} looks good!")
            good_files.append(file_description)

    return {
        "good": good_files,
        "too_many_total_rows_missing": too_many_missing_rows,
        "too_many_consecutive_rows_missing": too_many_consecutive_missing_rows
    }

