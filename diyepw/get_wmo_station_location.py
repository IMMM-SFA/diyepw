import os
import pkg_resources
import pandas as pd


def get_wmo_station_location(wmo_station_number: int):
    """
        Get the state, and county associated with a WMO station
        :param wmo_station_number: The WMO Station ID of the weather station to get location information for
        :return: Either a dict with fields "state" and "county", or None if no information is available for
            the passed WMO Station ID
    """
    wmo_station_info_filepath = pkg_resources.resource_filename('diyepw', 'data/Weather_Stations_by_County.csv')

    if not os.path.exists(wmo_station_info_filepath):
        raise Exception("Missing WMO station info file at " + wmo_station_info_filepath)

    wmo_station_info = pd.read_csv(wmo_station_info_filepath)

    station_of_interest = wmo_station_info[wmo_station_info['Station WMO Identifier'] == wmo_station_number]

    if len(station_of_interest.index) == 0:
        return None

    station_of_interest = station_of_interest.iloc[0]

    return {
        "state": station_of_interest.State,
        "county": station_of_interest.County
    }
