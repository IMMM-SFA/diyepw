import unittest
import diyepw
import os
import numpy.testing


class AthenaClientTest(unittest.TestCase):
    """
    Tests for the diyepw.Meteorology class.
    """

    def test_process_tmy3_file(self) -> None:
        """
        Test that a TMY3 (typical meteorological year EPW file) can be correctly read into a Meteorology instance
        :return:
        """
        meteorology = diyepw.Meteorology.from_tmy3_file(
            os.path.join("files", "test_tmy3.epw")
        )

        # Helper function to test the properties of Meteorology - test that they have the expected
        # value from the file, then that they have the expected value after it's been written
        def test_get_set(attr_name, initial_value, new_value):
            self.assertEqual(getattr(meteorology, attr_name), initial_value)
            setattr(meteorology, attr_name, new_value)
            self.assertEqual(getattr(meteorology, attr_name), new_value)

        test_get_set("city", "Test City", "New City Name")
        test_get_set("country", "Test Country", "New Country Name")
        test_get_set("latlong", (34.73,-92.233), (33.8121, -117.919))
        test_get_set("elevation", 78.0, 50.)
        test_get_set("state", "WA", "CA")
        test_get_set("station_number", "123456", "654321")
        test_get_set("timezone_gmt_offset", -6., -8.)

        # Test that at least one row of observations has been read in correctly
        observations = meteorology.observations
        numpy.testing.assert_almost_equal(observations.iloc[0].values, [
            1982., 1., 1., 1., 0., 5., -.6, 68., 100900., 0., 0., 308.,
            0., 0., 0., 0., 0., 0., 0., 340., 4.6, 10., 10., 8., 1370.,
            9., 999999999, 8., 0., 0., 88., 0., 0., 1.
        ])

    def test_netcdf_file(self) -> None:
        """
        Test that a NETCDF file can be correctly read into a Meteorology instance
        :return:
        """
        meteorology = diyepw.Meteorology.from_netcdf_file(
            os.path.join("files", "NLDAS_FORA0125_H.A20160301.0000.002.grb.SUB.nc4")
        )

if __name__ == '__main__':
    unittest.main()
