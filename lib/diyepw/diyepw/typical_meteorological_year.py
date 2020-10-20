import numpy as np
import pandas as pd
import os
import datetime
import calendar
import typing

class TypicalMeteorologicalYear:
    """
    Represents a Typical Meteorological Year (TMY) file; a dataset made up of a year of
    typical hourly meteorological measurements at a given location.

    Attributes:
        _station_number The identification number of the weather station that made the observations
        _headers - Array - Header file data taken from an input file
        _latitude - float - Latitude at which the data was observed
        _longitude - float - Longitude at which the data was observed
        _data_source - string - Currently always "NOAA_TMY," identifies the source of the data
        _city - str - The name of the city in which the data was observed
        _state - str - The name of the city in which the data was observed
        _country - str - The name of the city in which the data was observed
        _timezone_gmt_offset - float - The timezone where the data was observed, expressed as the difference
            from GMT
        _elevation - float - The elevation at which the data was observed in meters above sea level
        _comment - str - A comment string describing the TMY file
        _observations - DataFrame - Data representing the year's observations
    """

    def __init__(self):
        self._data_source = 'NOAA_TMY3' # Currently hard-coded because we only process NOAA .tmy3 files

        self._station_number = None
        self._headers = None
        self._latitude = None
        self._longitude = None
        self._city = None
        self._state = None
        self._country = None
        self._timezone_gmt_offset = None
        self._elevation = None
        self._comment = None
        self._observations = None

    @property
    def station_number(self):
        return self._station_number
    @station_number.setter
    def station_number(self, station_number:int):
        self._station_number = station_number

    @property
    def latlong(self):
        return self._latitude, self._longitude
    @latlong.setter
    def latlong(self, latlong:typing.Tuple[int, int]):
        self._latitude, self._longitude = latlong

    @property
    def city(self):
        return self._city
    @city.setter
    def city(self, city:str):
        self.city = city

    @property
    def state(self):
        return self._state
    @state.setter
    def state(self, state:str):
        self._state = state

    @property
    def country(self):
        return self._country
    @country.setter
    def country(self, country:str):
        self._country = country

    @property
    def timezone_gmt_offset(self):
        return self._timezone_gmt_offset
    @timezone_gmt_offset.setter
    def timezone_gmt_offset(self, timezone_gmt_offset:int):
        self._timezone_gmt_offset = timezone_gmt_offset

    @property
    def elevation(self):
        return self._elevation
    @elevation.setter
    def elevation(self, elevation:int):
        self._elevation = elevation

    # adapted from https://github.com/SSESLab/laf/blob/master/LAF.py
    ####################################################################################################################
    # Write new EPW file
    ####################################################################################################################
    def write_epw(self, save_path):
        first_observation = {k:v[0] for (k, v) in self._observations[0:1].items()}

        filename_epw = "{country}_{state}_{city}.{station}_AMY_{year}.epw".format(
            country=self._country,
            state=self._state,
            city=self._city,
            station=self._station_number,
            year=int(first_observation["year"])
        ).replace(' ', '-')

        location_header = ",".join([str(i) for i in [
            'LOCATION', self._city, self._state, self._country, 'customized weather file', self._station_number,
            self._latitude, self._longitude, self._timezone_gmt_offset, self._elevation
        ]])
        first_observation_date = datetime.date(
            year=int(first_observation["year"]),
            month=int(first_observation["month"]),
            day=int(first_observation["day"])
        )
        first_day_of_week = calendar.day_name[first_observation_date.weekday()]

        with open(os.path.join(save_path, filename_epw), 'w') as epw_file:
            epw_file.write("\n".join([
                location_header,
                "\n".join(self._headers[1:5]),
                self._comment,

                'COMMENTS 2, TMY3 data from energyplus.net/weather supplemented with NOAA ISD Lite data from ' +
                'https://www1.ncdc.noaa.gov/pub/data/noaa/isd-lite/ for an actual meteorological year (AMY)',

                'DATA PERIODS,1,1,Data,' + first_day_of_week + ', 1/1, 12/31'
            ]) + "\n")
            epw_file.write(self._observations.to_csv(header=False))

    # adapted from https://github.com/SSESLab/laf/blob/master/LAF.py
    @staticmethod
    def from_tmy3_file(file_path:str):
        """
        Create an instance of this class based on a tmy3 file

        :param file_path: Path to a TMY file. For the definition of a tmy3 file,
        see https://www.nrel.gov/docs/fy08osti/43156.pdf
        :return:
        """
        instance = TypicalMeteorologicalYear()
        tmy3_file = open(file_path)

        ############################
        # Read TMY3 header
        ############################
        instance._headers = []
        for i in range(0, 8):
            line = tmy3_file.readline().strip()
            instance._headers.append(line)
        tmy3_file.close()

        first_line = instance._headers[0].split(',')
        instance._city = first_line[1]
        instance._state = first_line[2]
        instance._country = first_line[3]
        instance._station_number = first_line[5]
        instance._latitude = float(first_line[6])
        instance._longitude = float(first_line[7])
        instance._timezone_gmt_offset = float(first_line[8])
        instance._elevation = float(first_line[9])

        instance._comment = instance._headers[5]

        ############################
        # Read TMY3 data
        ############################
        data = np.genfromtxt(file_path, delimiter=',', skip_header=8)
        instance._observations = pd.DataFrame(data={
            "year":           data[:, 0],
            "month":          data[:, 1],
            "day":            data[:, 2],
            "hour":           data[:, 3],
            "minute":         data[:, 4],
            "Tdb":            data[:, 6],
            "Tdew":           data[:, 7],
            "RH":             data[:, 8],
            "Patm":           data[:, 9],
            "ExHorRad":       data[:, 10],
            "ExDirNormRad":   data[:, 11],
            "HorIR":          data[:, 12],
            "GHRad":          data[:, 13],
            "DNRad":          data[:, 14],
            "DHRad":          data[:, 15],
            "GHIll":          data[:, 16],
            "DNIll":          data[:, 17],
            "DHIll":          data[:, 18],
            "ZenLum":         data[:, 19],
            "Wdir":           data[:, 20],
            "Wspeed":         data[:, 21],
            "TotSkyCover":    data[:, 22],
            "OpSkyCover":     data[:, 23],
            "Visib":          data[:, 24],
            "CeilH":          data[:, 25],
            "PresWeathObs":   data[:, 26],
            "PresWeathCodes": data[:, 27],
            "PrecWater":      data[:, 28],
            "AerOptDepth":    data[:, 29],
            "SnowDepth":      data[:, 30],
            "DSLS":           data[:, 31],
            "Albedo":         data[:, 32],
            "LiqPrecDepth":   data[:, 33],
            "LiqPrecQuant":   data[:, 34]
        })

        return instance