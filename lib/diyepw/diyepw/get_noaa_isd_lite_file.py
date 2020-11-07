import urllib.request as _request
import re as _re
import gzip as _gzip
import os as _os
import tempfile as _tempfile

def get_noaa_isd_lite_file(wmo_index:int, year:int, output_dir:str = None) -> str:
    """
    Given a WMO index and a year, retrieve the corresponding NOAA ISD Lite AMY file
    :param wmo_index:
    :param year:
    :param output_dir: Optional output directory - if not specified, the file will be saved to a temporary directory.
        If the directory already contains a NOAA ISD Lite file matching the requested WMO Index and year, then a new
        file will not be downloaded from NOAA and that file's path will be returned
    :return: The path to the NOAA ISD Lite file
    """
    if output_dir is None:
        output_dir = _tempfile.mkdtemp()

    # Retrieve the NOAA ISD Lite catalog for the requested year
    catalog_url = f"https://www1.ncdc.noaa.gov/pub/data/noaa/isd-lite/{year}/"
    with _request.urlopen(catalog_url) as response:
        html = response.read().decode('utf-8')

    # Find the filename in the catalog that matches the requested WMO index
    match = _re.search(f'href="({wmo_index}-\d*-{year}.gz)"', html)
    if match is None:
        raise Exception(f"No ISD Lite file for WMO index {wmo_index} and year {year} could be found at {catalog_url}")
    file_name_gz = match.groups()[0]

    # Download the ISD Lite file and decompress it, then save the decompressed file
    isd_lite_file_url = catalog_url + file_name_gz
    epw_gz_file_handle, epw_gz_file_path = _tempfile.mkstemp()
    epw_file_path = _os.path.join(output_dir, file_name_gz.replace(".gz", ".epw"))
    with _request.urlopen(isd_lite_file_url) as response, open(epw_gz_file_handle, 'wb') as epw_gz_file:
        epw_gz_file.write(response.read())
    with _gzip.open(epw_gz_file_path, 'rb') as epw_gz_file, open(epw_file_path, 'w') as epw_file:
        epw_file.write(epw_gz_file.read().decode('utf-8'))

    return epw_file_path