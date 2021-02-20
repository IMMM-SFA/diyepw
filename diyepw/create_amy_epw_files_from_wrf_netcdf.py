import xarray
import pandas as pd
import numpy as np
import os
import diyepw
import tempfile
from typing import Tuple, Dict, List
from functools import lru_cache

from ._logging import _logger

def _convert_wind_vectors_to_speed_and_dir(u: pd.Series(float), v: pd.Series(float)) -> Tuple[pd.Series, pd.Series]:
    """
    Convert wind data in vector form into speed and dir
    :param u: The east/west component of the wind's movement
    :param v: The north/south component of the wind's movement
    :return: The wind's speed (in meters/sec) and direction (in degrees)
    """
    # Use the Pythagorean Theorem to get the amplitude of the combined vectors, which is the
    # hypotenuse of a right triangle with the two vectors as the two sides
    speed = np.sqrt(u**2+v**2)

    # Take the arctangent of v/u to derive the angle of the hypotenuse, which gives us our wind direction
    direction = np.degrees(np.arctan2(v, u))

    return speed, direction

@lru_cache()
def _get_lat_long_by_wmo_index(wmo_index:int) -> Tuple[float, float]:
    """
    :param wmo_index: WMO ID of a weather station
    :return: The latitude and longitude of the weather station
    """
    weather_station_table = pd.read_csv('/Users/benjamin/Code/diyepw/diyepw/diyepw/data/Weather_Stations_by_County.csv')
    weather_station_row = weather_station_table[weather_station_table["Station WMO Identifier"] == int(wmo_index)].iloc[0]
    return float(weather_station_row["Station Latitude"]), float(weather_station_row["Station Longitude"])

def _get_wrf_data(wmo_indexes: List[int], year: int, wrf_netcdf_dir: str) -> Dict[int, pd.DataFrame]:
    """
    Retrieve WRF NetCDF data associated with a set of weathers stations for a given year.

    :param wmo_indexes: The WMO Indexes of the weather stations for which to retrieve data - the data will
        be retrieved for the lat/long coordinate in the WRF NetCDF file that is closest to the lat/long of
        the weather station.
    :param year: The year for which to retrieve observed data.
    :param wrf_netcdf_dir: The directory in which WRF NetCDF files can be found. The files are expected to be
        organized within this directory in subdirectories named after the year whose data is contained in each:
        <wrf_netcdf_dir>/
            2009/
                <wrf_netcdf_file>...
            2010/
                <wrf_netcdf_file>...
            ...
    :return: dict in the form { <wmo_index>: DataFrame }, where each DataFrame contains a year's observations
        for the lat/long closest to the weather station's location.
    """

    if not os.path.exists(wrf_netcdf_dir) or not os.path.isdir(wrf_netcdf_dir):
        raise Exception(wrf_netcdf_dir + " is not a directory")

    year_folder = os.path.join(wrf_netcdf_dir, str(year))
    if not os.path.exists(year_folder) or not os.path.isdir(year_folder):
        raise Exception(f"{wrf_netcdf_dir} does not contain the expected directory '{year}/' containing that year's WRFNetCDF files")

    filenames = os.listdir(year_folder)
    filenames.sort() # Not really necessary, but feels right, and makes it easier to watch progress through the files

    dfs_by_wmo_index = dict([(index, None) for index in wmo_indexes])
    for filename in filenames:
        _logger.info(f"Processing NetCDF file {filename}...")

        # Parse the NetCDF file and extract out the data closest to that lat/long
        ds = xarray.open_dataset(os.path.join(year_folder, filename))

        # The WRF NetCDF files are not indexed properly. We have contacted LBNL about this and they've declined
        # to make any changes, so we have to reindex so that .sel() will work correctly. The original coordinate
        # variables (XLONG, XLAT, Times) are then unnecessary because the indexes contain the correct values.
        ds = ds.reindex(Time=ds.Times, west_east=ds.XLONG[0,0,:], south_north=ds.XLAT[0,:,0])
        ds = ds.drop_vars(["XLONG", "XLAT", "Times"])

        # Pull out just the data for the lat/long coordinate that is the closest to each weather station
        for wmo_index in wmo_indexes:
            _logger.info(f"Processing WMO index {wmo_index}...")
            (lat, long) = _get_lat_long_by_wmo_index(wmo_index)
            ds_at_lat_long = ds.sel({ "south_north":lat, "west_east":long }, method='nearest', tolerance=1, drop=True)

            # Convert the DataSet, which is now one-dimensional, having data for each variable with respect only to
            # time, into a two-dimensional (time x variable) Pandas array. We then transpose() because this conversion
            # results in time being the columns and variables being the rows.
            ds_at_lat_long = ds_at_lat_long.to_array().to_pandas().transpose()

            # Append the data to our DataFrame, which will ultimately contain the full year's data
            if dfs_by_wmo_index[wmo_index] is None:
                dfs_by_wmo_index[wmo_index] = ds_at_lat_long
            else:
                dfs_by_wmo_index[wmo_index] = pd.concat([dfs_by_wmo_index[wmo_index], ds_at_lat_long])

    return dfs_by_wmo_index

def create_amy_epw_files_from_wrf_netcdf(
        wmo_indexes: List[int],
        years: List[int],
        wrf_netcdf_dir: str,
        output_path: str=None,
        allow_downloads: bool = False) -> List[str]:
    """
    For a set of WMO Indexes and years, generate AMY (actual meteorological year) EPW files based on WRF NetCDF files.
    As with other AMY EPW files generated by the DIYEPW package, this is done by taking a TMY (typical meteorological
    year) EPW and replacing some of the fields with actual observed values to create an EPW that represents actually
    observed conditions. The fields that are replaced and thus represent actual observations in the generated EPW
    are:
        Patm: atmospheric pressure
        LiqPrecDepth: Liquid precipitation depth
        Tdb: Dry-bulb temperature
        Wspeed: Wind speed
        Wdir: Wind direction
        RH: Relative Humidity

    :param wmo_indexes: The WMO Indexes for which to generate EPWs
    :param years: The years for which to generate EPWs
    :param wrf_netcdf_dir: The directory in which WRF NetCDF files can be found. The files are expected to be
        organized within this directory in subdirectories named after the year whose data is contained in each:
        <wrf_netcdf_dir>/
            2009/
                <wrf_netcdf_file>...
            2010/
                <wrf_netcdf_file>...
            ...
    :param output_path: The directory into which the generated EPW files should be written
        If not defined, a temporary directory will be created
    :param allow_downloads: If True, then TMY data will automatically be downloaded, otherwise the function will fail
        with an exception if any TMY files are not present that are required for generating the requested EPWs
    :return: Paths to the EPW files generated
    """

    if output_path is None:
        output_path = tempfile.mkdtemp()

    file_paths = []

    for year in years:
        # We need to process each WRF file for a year (collected together in a directory), and stitch all their data together
        # into a single Pandas array
        dfs_by_wmo_index = _get_wrf_data(wmo_indexes, year, wrf_netcdf_dir)

        for wmo_index in wmo_indexes:
            df = dfs_by_wmo_index[wmo_index]

            # The LBNL example data is missing records for the last two hours of the year. :(
            # TODO: Remove this when LBNL delivers complete data
            df.loc[b'2009-12-31_22:00:00'] = df.loc[b'2009-12-31_21:00:00']
            df.loc[b'2009-12-31_23:00:00'] = df.loc[b'2009-12-31_21:00:00']

            # Create a TMY meteorology instance, so that we can inject the observed AMY data from the WRF files and
            # generate an AMY EMP from the result
            tmy_file = diyepw.get_tmy_epw_file(wmo_index, allow_downloads=allow_downloads)
            meteorology = diyepw.Meteorology.from_tmy3_file(tmy_file)

            # Atmospheric Pressure, requires no conversion
            meteorology.set("Patm", df.PSFC)

            # Liquid precipitation depth - just sum up the values, as liquid precipitation is split across three
            # variables in WRF NetCDF
            meteorology.set("LiqPrecDepth", np.sum([df.RAINC, df.RAINSH, df.RAINNC]))

            # Dry-bulb temperature - Convert K -> C
            meteorology.set("Tdb", df.T2 + 273.15)

            # - Wind Direction & Speed (V10, U10 - convert from vectors)
            wind_speed, wind_dir = _convert_wind_vectors_to_speed_and_dir(df.U10, df.V10)
            meteorology.set("Wspeed", wind_speed)
            meteorology.set("Wdir", wind_dir)

            # Relative humidity conversion algorithm taken from here: https://www.mcs.anl.gov/~emconsta/relhum.txt:
            #
            # define relative humidity matching the algorithm used for hindcasts
            # let pq0 = 379.90516
            # let a2 = 17.2693882
            # let a3 = 273.16
            # let a4 = 35.86
            # let /title="relative humidity" /units="fraction" f_rh2 = q2 / ( (pq0 / psfc) * exp(a2 * (t2 - a3) / (t2 - a4)) )
            #
            # where
            #       q2 = Q2 variable from wrf
            #       t2 = T2 variable from wrf
            #       psfc = surface pressure from WRF
            #
            # This calculates 2 m (approximately) relative humidity.
            meteorology.set("RH", df.Q2 / (379.90516 / df.PSFC) * np.exp(17.2693882 * (df.T2 - 273.16) / (df.T2 - 35.86)))

            # Now that we have replaced as much data from the TMY meteorology as possible from the data in the WRF NetCDF,
            # all that is left to do is write out the file as an EPW
            file_path = os.path.join(output_path, f"{wmo_index}_{year}.epw")
            meteorology.write_epw(file_path)
            print(f"Wrote data for WMO {wmo_index} and year {year}: {file_path}")
            file_paths.append(file_path)

    return file_paths
