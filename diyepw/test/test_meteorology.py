import unittest
import diyepw


class MeteorologyTest(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        self._meteorology = diyepw.Meteorology()

    def test_property_setters_and_getters__good_values(self):
        """
        Tests the Meteorology class's @property-tagged setter/getter methods, confirming that
        when valid values are submitted, they properly store the value and the same value is returned
        from the equivalent getter method
        :return:
        """
        test_values = {
            'station_number' : [123456, 654321],
            'latlong' : [(85.2, -17.3), (-12.4, 18)],
            'city' : ['Richland', 'Neuenhaus'],
            'state' : ['WA', 'AL'],
            'country' : ["United States of America", "Peoples' Republic of Testcaseistan"],
            'timezone_gmt_offset' : [-6, 8],
            'elevation' : [2431, -5]
        }

        # Assert that, for each test value defined above, the identical value is returned from the
        # property getter after being assigned by the property setter
        for property_name in test_values:
            for test_value in test_values[property_name]:
                setattr(self._meteorology, property_name, test_value)
                self.assertEqual(test_value, getattr(self._meteorology, property_name))

    def test_property_setters__bad_values(self):
        """
        Tests that the Meteorology class's @property-tagged setter methods properly raise Exceptions when
        passed invalid values
        :return:
        """
        test_values = {
            'station_number' : [
                -6, # Negative
                "Banana", # Not numerical
                44321, # Too short for a WMO index
                8888888 # Too long for a WMO index
            ],
            'latlong' : [5, (91, 0), (0, -181)], # Latlong has to be a duple of valid lat/long values
            'timezone_gmt_offset' : [-13, 13], # Timezone offsets must be in the range +/-12
            'elevation' : ["a frippery"] # Elevation must be an integer
        }

        # Assert that, for each test value defined above, an Exception is raised by the attempt to set it
        for property_name in test_values:
            for test_value in test_values[property_name]:
                with self.assertRaises(
                        Exception,
                        msg=f"Setting Meteorology property {property_name} to {test_value} d"
                            f"id not cause an Exception to be raised"
                ):
                    setattr(self._meteorology, property_name, test_value)

if __name__ == '__main__': # pragma: no cover
    unittest.main()
