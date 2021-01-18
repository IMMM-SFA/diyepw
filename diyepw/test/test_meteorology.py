import unittest
import diyepw
import pkg_resources
import random


class MeteorologyTest(unittest.TestCase):
    """
    Tests of the behavior of the diyepw.Meteorology class
    """

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

    def test_create_from_tmy3(self):
        """
        Tests that observations from a known TMY3 file result in an instance with the expected values
        :return:
        """
        tmy_file_path = pkg_resources.resource_filename('diyepw', 'test/files/TEST_TMY3.epw')
        meteorology = diyepw.Meteorology.from_tmy3_file(tmy_file_path)

        self.assertEqual(meteorology.city, "Testville")
        self.assertEqual(meteorology.country, "USA")
        self.assertEqual(meteorology.elevation, 78.)
        self.assertEqual(meteorology.latlong, (32.1, -90.23009))
        self.assertEqual(meteorology.station_number, '799999')
        self.assertEqual(meteorology.timezone_gmt_offset, -6)

        observations = meteorology.observations
        expected_columns = [
            'year', 'month', 'day', 'hour', 'minute', 'Tdb', 'Tdew', 'RH', 'Patm', 'ExHorRad', 'ExDirNormRad', 'HorIR',
            'GHRad', 'DNRad', 'DHRad', 'GHIll', 'DNIll', 'DHIll', 'ZenLum', 'Wdir', 'Wspeed', 'TotSkyCover',
            'OpSkyCover', 'Visib', 'CeilH', 'PresWeathObs', 'PresWeathCodes', 'PrecWater', 'AerOptDepth', 'SnowDepth',
            'DSLS', 'Albedo', 'LiqPrecDepth', 'LiqPrecQuant'
        ]
        for col in expected_columns:
            self.assertIn(col, observations.columns)

    def test_validation(self):
        """
        Tests that the validation rules are properly applied
        :return:
        """
        tmy_file_path = pkg_resources.resource_filename('diyepw', 'test/files/TEST_TMY3.epw')
        meteorology = diyepw.Meteorology.from_tmy3_file(tmy_file_path)

        # Initially there should be no validation errors in the test file
        epw_violations = meteorology.validate_against_epw_rules()
        self.assertEqual(len(epw_violations), 0, msg=f"Expected 0 EPW validation errors but got {len(epw_violations)}")

        invalid_values = {
            'Tdb': [-71, 71],
            'Tdew': [-71, 71],
            'Patm': [30999, 120001],
            'Wspeed': [-1, 41],
            'Wdir': [-1, 361]
        }
        # Intentionally introduce validation errors and confirm that the expected error appears
        for col in invalid_values:
            original_values = meteorology.observations.loc[:, col].copy()
            for value in invalid_values[col]:
                changed_values = original_values.copy()
                changed_values.iloc[random.randint(0, len(changed_values) - 1)] = value
                meteorology.set(col, changed_values)
                epw_violations = meteorology.validate_against_epw_rules()
                self.assertEqual(
                    len(epw_violations),
                    1,
                    f"Expected 1 EPW validation error but got {len(epw_violations)}. Violations were: {epw_violations}"
                )
                self.assertIn(f"{col} must be in the range", epw_violations[0])

                # Replace the original values after each test so that only a single error is ever present
                meteorology.set(col, original_values)



if __name__ == '__main__': # pragma: no cover
    unittest.main()
