import urllib.request as request
import re
import os
import pandas as pd

def get_noaa_isd_lite_file(wmo_index:int, year:int, output_dir:str = None, force_update = False) -> str:
    """
    Given a WMO index and a year, retrieve the corresponding NOAA ISD Lite AMY file
    :param wmo_index:
    :param year:
    :param output_dir: Optional output directory - if not specified, the file will be saved to a package directory.
        If the directory already contains a NOAA ISD Lite file matching the requested WMO Index and year, then a new
        file will not be downloaded from NOAA and that file's path will be returned
    :param force_update: Pass True to force a new ISD Lite file to be downloaded, even if it already exists in the
       output directory.
    :return: The path to the NOAA ISD Lite file
    """
    if output_dir is None:
        this_dir = os.path.dirname(os.path.realpath(__file__))
        output_dir = os.path.join(this_dir, 'files', 'noaa_isd_lite_files')

    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    # On the NOAA website, the ISD Lite files are named with a third number between WMO and year, but
    # since we don't use that third number for anything and it complicates identifying a file for a
    # WMO/Year combination, we simplify the name to only contain the values we care about
    file_name = f"{wmo_index}-{year}.gz"
    file_path = os.path.join(output_dir, file_name)

    # Download the ISD Lite file if it's not already in the output directory
    if force_update or not os.path.exists(file_path):
        url = _get_noaa_isd_lite_file_url(year, wmo_index)
        with request.urlopen(url) as response:
            with open(file_path, 'wb') as downloaded_file:
                downloaded_file.write(response.read())

    return file_path

def _get_noaa_isd_lite_file_url(year:int, wmo_index:int) -> str:
    catalog = _get_noaa_isd_lite_file_catalog(year)
    file_name = list(catalog.loc[catalog['wmo_index'] == wmo_index]['file_name'])[0]
    return f"https://www1.ncdc.noaa.gov/pub/data/noaa/isd-lite/{year}/{file_name}"

def _get_noaa_isd_lite_file_catalog(year:int, catalog_dir=None, force_update=False) -> pd.DataFrame:
    """
    Retrieve the list of all NOAA ISD Lite files for North America (WMO indices starting with 7) for a given year.
    If the file is not already present, one will be downloaded. Files are named after the year whose files they
    describe.
    :param year:
    :param catalog_dir: The directory in which to look for the file, and into which the file will be written if
        downloaded
    :param force_update: If set to True, a new copy of the catalog file will be downloaded and will overwrite the
        current one if it already exists.
    :return: A Pandas Dataframe containing a set of file names. The file names can be
        appended to the URL https://www1.ncdc.noaa.gov/pub/data/noaa/isd-lite/{year}/ to download the files from
        NOAA
    """
    if catalog_dir is None:
        this_dir = os.path.dirname(os.path.realpath(__file__))
        catalog_dir = os.path.join(this_dir, 'files', 'noaa_isd_lite_catalogs')

    if not os.path.exists(catalog_dir):
        raise Exception(f"Directory {catalog_dir} does not exist")

    file_path = os.path.join(catalog_dir, str(year))

    # If the catalog file already exists, we'll read ient. If it doesn't, we'll download it, import it into a
    # dataframe, and then save that so that it exists the next time we need it.
    if os.path.exists(file_path) and not force_update:
        catalog = pd.read_csv(file_path)
    else:
        catalog = pd.DataFrame(columns=['wmo_index', 'file_name'])

        # Retrieve the NOAA ISD Lite catalog for the requested year
        with request.urlopen(f"https://www1.ncdc.noaa.gov/pub/data/noaa/isd-lite/{year}/") as response:
            # Process the file: Look for an href linking to a file that starts with "7" (indicating it is
            # a North American WMO) and put all such referenced file names into the catalog file
            html = response.read().decode('utf-8')
            for line in html.splitlines():
                # Regex: Match hrefs pointing to files in the form #-#-#.gz, where the first # starts with a 7.
                # Capture groups: The big capture group gets the file name, and the small one gets the WMO
                match = re.search(f'href="((7\d+)-.*\.gz)"', line)
                if match is not None:
                    file_name, wmo_index = match.groups()
                    catalog = catalog.append({'wmo_index': int(wmo_index), 'file_name': file_name}, ignore_index=True)

            catalog.to_csv(file_path, index=False)

    return catalog
