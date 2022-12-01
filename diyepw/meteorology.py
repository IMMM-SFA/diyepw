import os
import pandas as pd
import datetime
import calendar
import typing

class Meteorology:
    """
    Represents a time series of meteorological measurements at a given location.

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

    _RANGES = {
        'Tdb': (-70, 70),
        'Tdew': (-70, 70),
        'Patm': (31000, 120000),
        'Wspeed': (0, 40),
        'Wdir': (0, 360)
    }

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
        return int(self._station_number)
    @station_number.setter
    def station_number(self, station_number:int):
        if station_number < 100000 or station_number > 999999:
            raise Exception("station_number must be a six-digit number")
        self._station_number = int(station_number)

    @property
    def latlong(self):
        return self._latitude, self._longitude
    @latlong.setter
    def latlong(self, latlong:typing.Tuple[float, float]):
        lat, long = latlong

        if abs(lat) > 90:
            raise Exception("Latitude must be in the range -90 - 90")
        if abs(long) > 180:
            raise Exception("Longitude must be in the range -180 - 180")

        self._latitude, self._longitude = latlong

    @property
    def city(self):
        return self._city
    @city.setter
    def city(self, city:str):
        self._city = city

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
        if abs(timezone_gmt_offset) > 12:
            raise Exception("timezone_gmt_offset must be in the range -12 - 12")
        self._timezone_gmt_offset = int(timezone_gmt_offset)

    @property
    def elevation(self):
        return self._elevation
    @elevation.setter
    def elevation(self, elevation:int):
        self._elevation = int(elevation)

    @property
    def observations(self):
        return self._observations
    @observations.setter
    def observations(self, observations:int):
        self._observations = observations

    def set(self, column_name:str, val):
        """
        Overwrite one of the columns in this instance's observations
        :param column_name: Must be the name of one of the columns in this instance's observations
        :param val: Mixed.
           If val is a single value, every value of the named column will be set to that value
           If val is a list or pandas.Series, it must contain the same number of items as there are
               rows in this instance's observations, and will replace those values for the named column
        :return:
        """
        if not column_name in self._observations:
            raise Exception("{c} is not one of the columns in this meteorological year's observations".format(c=column_name))

        # If we are passed a Pandas Series, just convert it to a list and let the generic list handling take care of it
        if isinstance(val, pd.Series):
            val = list(val)

        # If we have a list, we will check that its length is identical to that of the observation set, and that it has
        # consistently typed data of the correct type before using it
        if isinstance(val, list):
            # Lists replace the items in a column one-to-one, so we have to ensure that the passed list contains
            # exactly the same number of elements as our observations have rows
            if len(val) != len(self._observations):
                raise Exception("""
                    This meteorological year has {my_num} observations, but you passed a 
                    list of {your_num} replacement values
                """.format(my_num=len(self._observations), your_num=len(val))
                )

        # An assignment works here regardless of whether val is a list or a single item. If it's a list, the whole
        # column will be replaced with the values from the list. If it's a single item, that item will be duplicated
        # to fill the entire column
        self._observations[column_name] = val

    # adapted from https://github.com/SSESLab/laf/blob/master/LAF.py
    ####################################################################################################################
    # Write new EPW file
    ####################################################################################################################
    def write_epw(self, save_path):
        first_observation = {k:v[0] for (k, v) in self._observations[0:1].items()}

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

        with open(save_path, 'w', newline='') as epw_file:
            epw_file.writelines([
                location_header,
                os.linesep,
                os.linesep.join(self._headers[1:5]),
                os.linesep,
                self._comment,
                os.linesep,

                'COMMENTS 2, TMY3 data from energyplus.net/weather supplemented with NOAA ISD Lite data from ' +
                'https://www1.ncdc.noaa.gov/pub/data/noaa/isd-lite/ for an actual meteorological year (AMY)',
                os.linesep,
                'DATA PERIODS,1,1,Data,' + first_day_of_week + ', 1/1, 12/31',
                os.linesep
            ])
            self._observations.to_csv(epw_file, header=False, index=False)

    # adapted from https://github.com/SSESLab/laf/blob/master/LAF.py
    @staticmethod
    def from_tmy3_file(file_path:str):
        """
        Create an instance of this class based on a tmy3 file

        :param file_path: Path to a TMY file. For the definition of a tmy3 file,
        see https://www.nrel.gov/docs/fy08osti/43156.pdf
        :return:
        """
        instance = Meteorology()

        ############################
        # Read TMY3 header
        ############################
        with open(file_path) as tmy3_file:
            instance._headers = []
            for i in range(0, 8):
                line = tmy3_file.readline().strip()
                instance._headers.append(line)

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
        instance._observations = pd.read_csv(
            file_path,
            names=[
                "year",
                "month",
                "day",
                "hour",
                "minute",
                "Flags",
                "Tdb",
                "Tdew",
                "RH",
                "Patm",
                "ExHorRad",
                "ExDirNormRad",
                "HorIR",
                "GHRad",
                "DNRad",
                "DHRad",
                "GHIll",
                "DNIll",
                "DHIll",
                "ZenLum",
                "Wdir",
                "Wspeed",
                "TotSkyCover",
                "OpSkyCover",
                "Visib",
                "CeilH",
                "PresWeathObs",
                "PresWeathCodes",
                "PrecWater",
                "AerOptDepth",
                "SnowDepth",
                "DSLS",
                "Albedo",
                "LiqPrecDepth",
                "LiqPrecQuant",
            ],
            dtype={
                "year": int,
                "month": int,
                "day": int,
                "hour": int,
                "minute": int,
                "Flags": str,
            },
            skiprows=8,
            index_col=False,
        )

        return instance

    def validate_against_epw_rules(self) -> list:
        """
        Check all observations to see whether they violate any restrictions that would prevent them
        from being used in an EPW file

        :return: A list of validation errors
        """
        violations = []

        for col_name in self._RANGES:
            min_allowed, max_allowed = self._RANGES[col_name]
            min_observed = self._observations[col_name].min()
            max_observed = self._observations[col_name].max()
            if min_observed < min_allowed or max_observed > max_allowed:
                violations.append(f"{col_name} must be in the range {min_allowed}-{max_allowed}, but this set"
                                  f" of observations includes values in the range {min_observed}-{max_observed}")

        return violations