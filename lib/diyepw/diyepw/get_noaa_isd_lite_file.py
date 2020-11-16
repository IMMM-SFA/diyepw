import urllib.request as _request
import re as _re
import os as _os
import tempfile as _tempfile

# Buffer for the EPW catalog, which is a large HTML file that we don't want to have to download anew every time
# a new ISD Lite file is requested. Keys are the URLs, allowing multiple to be buffered, for example for multiple
# years
_catalog_html = {}

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

    catalog_url = f"https://www1.ncdc.noaa.gov/pub/data/noaa/isd-lite/{year}/"

    # Retrieve the NOAA ISD Lite catalog for the requested year, if it hasn't already been downloaded
    if not catalog_url in _catalog_html.keys():
        with _request.urlopen(catalog_url) as response:
            _catalog_html[catalog_url] = response.read().decode('utf-8')

    # Find the filename in the catalog that matches the requested WMO index and year
    match = _re.search(f'href="({wmo_index}-\d*-{year}\.gz)"', _catalog_html[catalog_url])
    if match is None:
        raise Exception(f"No ISD Lite file for WMO index {wmo_index} and year {year} could be found at {catalog_url}")
    file_name = match.groups()[0]

    # Download the ISD Lite file and save it
    isd_lite_file_url = catalog_url + file_name
    downloaded_file_path = _os.path.join(output_dir, file_name)
    with _request.urlopen(isd_lite_file_url) as response:
        with open(downloaded_file_path, 'wb') as downloaded_file:
            downloaded_file.write(response.read())

    return downloaded_file_path