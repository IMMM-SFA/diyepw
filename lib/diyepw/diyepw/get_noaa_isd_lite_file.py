import urllib.request as _request
import re as _re
import gzip as _gzip
import tempfile as _tempfile

def get_noaa_isd_lite_file(wmo_index:int, year:int):
    """
    Given a WMO index and a year, retrieve the corresponding NOAA ISD Lite AMY file
    :param wmo_index:
    :param year:
    :return:
    """

    # Retrieve the NOAA ISD Lite catalog for the requested year
    catalog_url = f"https://www1.ncdc.noaa.gov/pub/data/noaa/isd-lite/{year}/"
    with _request.urlopen(catalog_url) as response:
        html = response.read().decode('utf-8')

    # Find the filename in the catalog that matches the requested WMO index
    match = _re.search(f'href="({wmo_index}-\d*-{year}.gz)"', html)
    file_name = match.groups()[0]

    # Download the ISD Lite file and decompress it, then save the decompressed file
    isd_lite_file_url = catalog_url + file_name
    epw_gz_file_handle, epw_gz_file_path = _tempfile.mkstemp()
    with _request.urlopen(isd_lite_file_url) as response, open(epw_gz_file_handle, 'wb') as epw_gz_file:
        epw_gz_file.write(response.read())
    with _gzip.open(epw_gz_file_path, 'rb') as epw_gz_file, open('test.epw', 'w') as epw_file:
        epw_file.write(epw_gz_file.read().decode('utf-8'))