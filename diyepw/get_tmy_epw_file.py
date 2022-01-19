import tempfile
import urllib.request as request
import re
import os
import shutil
import pkg_resources
import pandas as pd
from zipfile import ZipFile
from urllib.error import URLError

from ._logging import _logger
from .exceptions import DownloadNotAllowedError

def get_tmy_epw_file(wmo_index:int, output_dir:str = None, allow_downloads:bool = False):
    """
    Given a WMO index, retrieve a TMY (typical meteorological year) EPW file for that location
    :param wmo_index:
    :param output_dir: Optional output directory - if not specified, the file will be saved to a directory in the
        diyepw package so that it can be reused in the future if needed. If the directory already contains a TMY
        EWP file matching the requested WMO Index, then a new file will not be downloaded, we will just return
        that file's path
    :param allow_downloads: Set to True to allow downloads if TMY3 files or the catalog containing their
        names and URLs to be downloaded from http://climate.onebuilding.org if not already present. If you want
        to use this method without permitting downloads, then the TMY3 files can be downloaded manually and put
        into the directory specified by output_dir (which defaults to data/tmy_epw_files/ in the package's own
        directory structure). In this case, the files must have names identical to those used by
        http://climate.onebuilding.org/WMO_Region_4_North_and_Central_America/USA_United_States_of_America/
    :return: The path to the TMY EPW file
    """
    _logger.debug(f"get_tmy_epw_file() - Retrieving TMY EPW file for WMO {wmo_index}")

    if output_dir is None: # pragma: no cover - Not worth the risk of having tests that fiddle with real project data
        output_dir = pkg_resources.resource_filename("diyepw", "data/tmy_epw_files")

    if not os.path.isdir(output_dir):
        raise Exception(f'The path {output_dir} is not a valid directory path')

    tmy3_file_catalog = _get_tmy3_file_catalog(allow_downloads=allow_downloads)
    tmy3_file_information = tmy3_file_catalog.loc[tmy3_file_catalog['wmo_index'] == int(wmo_index)]

    if len(tmy3_file_information) == 0:
        raise Exception(f"No TMY3 file appears to exist in our catalog for the WMO Index '{wmo_index}'")

    # Get the filename for the requested WMO index's TMY3 file. We swap the extension
    epw_file_name = tmy3_file_information.iloc[0]['file_name']
    epw_file_url  = tmy3_file_information.iloc[0]['url']
    epw_file_path = os.path.join(output_dir, epw_file_name)

    # Check whether we already have the TMY EPW file in our directory. If we do it would be a waste of time
    # to download it again.
    if os.path.exists(epw_file_path):
        _logger.info(f"TMY EPW file ({epw_file_path}) already exists, won't download again.")
        return epw_file_path

    # If the TMY EPW file is not already present in our directory, then we need to check that we've been given
    # permission to download missing files
    if not allow_downloads:
        raise DownloadNotAllowedError(
            f"The TMY3 file {epw_file_path} is not present. Pass allow_downloads=True to "
            f"allow the missing data to be automatically downloaded from {epw_file_url}"
        )

    # Download the ZIP file and decompress it. It contains a number of files including the EPW that we are looking for.
    tmp_file_handle, tmp_file_path = tempfile.mkstemp()
    tmp_dir = tempfile.mkdtemp()
    _logger.info(f"Downloading file from {epw_file_url} and saving to {epw_file_path}")
    try:
        with request.urlopen(epw_file_url) as response:
            with open(tmp_file_handle, 'wb') as downloaded_file:
                downloaded_file.write(response.read())
    except URLError: # pragma: no cover - Not worth the time to write a test that disables the internet just for one exception
        raise Exception(f"Failed to download TMY EPW file {epw_file_url} - are you connected to the internet?")
    except Exception as e: # pragma: no cover - This block is good for adding information to an Exception but can't be intentionally provoked
        raise Exception(f"Error downloading from {epw_file_url}: {e}")

    with ZipFile(tmp_file_path, 'r') as zip_file:
        zip_file.extractall(tmp_dir)

    # Move the EPW file from the temporary directory into which we extracted
    # the ZIP file into the directory storing our EPWs
    shutil.move(os.path.join(tmp_dir, epw_file_name), epw_file_path)

    # Delete the temporary files created in this call
    os.unlink(tmp_file_path)
    shutil.rmtree(tmp_dir)

    return epw_file_path

def _get_tmy3_file_catalog(allow_downloads:bool = False) -> pd.DataFrame:
    """
    Retrieves the catalog of TMY3 files, which contains a list of all WMOs in the United States, along with the
    names and download URLs of a TMY3 file for that WMO.

    :param allow_downloads: If True, and if the catalog is missing, then the catalog will be downloaded from
    http://climate.onebuilding.org and stored in this package's data directory. The catalog should not actually
    be missing unless it has been manually removed, as the DIYEPW package ships with a copy of the file already
    included.

    :return: A pandas DataFrame with the following columns:
        - wmo_index: The WMO Index of a weather station
        - file_name: The name of the TMY3 file corresponding to that WMO Index
        - url: The URL from which the TMY3 file can be downloaded
    """

    catalog_file_path = pkg_resources.resource_filename("diyepw", "data/tmy_epw_catalogs/tmy_epw_catalog.csv")

    # The sources we know of for TMY EPW files are http://climate.onebuilding.org and https://energyplus.net/weather;
    # we use the climate.onebuilding.org source here because it has all of the EPW files linked
    # from a single page, making it relatively easy to work with
    catalog_urls = (
        "http://climate.onebuilding.org/WMO_Region_4_North_and_Central_America/USA_United_States_of_America/",
        "http://climate.onebuilding.org/WMO_Region_4_North_and_Central_America/CAN_Canada/",
    )

    if os.path.exists(catalog_file_path):
        catalogs = [pd.read_csv(catalog_file_path)]  # put in a list for pd.concat
    else:
        # If the catalog is not already present, and the caller has allowed for downloads,
        # download the catalog file from the source site
        catalogs = []
        for catalog_url in catalog_urls:
            if not allow_downloads:
                raise DownloadNotAllowedError(
                    f"The TMY3 catalog file {catalog_file_path} is not present. Pass allow_downloads=True to "
                    f"allow the missing data to be automatically downloaded from {catalog_url}"
                )

            _logger.info(f"The TMY3 catalog file was not found at {catalog_file_path}, and allow_downloads is True, so "
                         f"the catalog will be downloaded from {catalog_url}")

            # Retrieve the TMY EPW catalog for the requested year.
            try:
                with request.urlopen(catalog_url) as response:
                    catalog_html = response.read().decode('utf-8')
            except URLError: # pragma: no cover - Not worth the time to write a test that disables the internet just for one exception
                raise Exception(f"Failed to connect to {catalog_url} - are you connected to the internet?")
            except Exception as e: # pragma: no cover - This block is good for adding information to an Exception but can't be intentionally provoked
                raise Exception(f"Error downloading from {catalog_url}: {e}")

            # Iterate over each line in the catalog HTML page, parsing out the file names for each TMY3 file that is
            # encountered
            catalog = pd.DataFrame(columns=['wmo_index', 'file_name', 'url'])
            for line in catalog_html.splitlines():
                # Regex: Match hrefs pointing to files in the form *.#_TMY3.zip, where the # is the WMO
                # represented by the file.
                # Capture groups: The big capture group gets the file name, and the small one gets the WMO
                # Second period before .zip is to catch TMY3 or TMYx.
                for match in re.finditer(r'href="([^"]*\.(\d{6})_TMY..zip)"', line):
                    file_path, wmo_index = match.groups()

                    # The file extension of the download URL is .zip, and points to an archive file containing a number
                    # of files. Within that archive is the TMY EPW file, which has the same name and the .epw extension.
                    file_name = file_path.split('/')[-1].replace('.zip', '.epw')

                    catalog = catalog.append({
                        'wmo_index': int(wmo_index),
                        'file_name': file_name,
                        'url': catalog_url + '/' + file_path
                    }, ignore_index=True)
            catalogs.append(catalog)

    catalogs = pd.concat(catalogs, ignore_index=True)
    catalogs.to_csv(catalog_file_path, index=False)
    return catalogs
