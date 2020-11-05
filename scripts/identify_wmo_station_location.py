import os
import pandas as pd


def identify_wmo_station_location(wmo_station_number):
    """Return the WMO station number, state, and county as a list provided with WMO station number as an input."""
    wmo_station_info_filename = 'Weather_Stations_by_County.csv'
    wmo_station_info_filepath = (os.path.join('../inputs/', wmo_station_info_filename))

    wmo_station_info = pd.read_csv(wmo_station_info_filepath)

    station_of_interest = wmo_station_info[wmo_station_info['Station WMO Identifier'] == wmo_station_number]

    if len(station_of_interest.index) < 1:
        print('Station not present in ' + wmo_station_info_filename)
        return

    station_of_interest = station_of_interest.iloc[0]

    station_state_county = [wmo_station_number, station_of_interest.State, station_of_interest.County]

    return station_state_county
