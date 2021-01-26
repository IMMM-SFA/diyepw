import unittest
import diyepw
import tempfile
import pvlib
import pandas as pd


class TmyCreateAmyEpwFilesForYearsAndWmosTest(unittest.TestCase):
    """
    Tests of the behavior of the create_amy_epw_files_for_years_and_wmos() function
    """

    def test_file_creation_with_download(self):
        """Verify the standard use case - files that are not already available being requested with
           downloads enabled"""
        years = [2015, 2016]
        wmo_indices = [725300, 725957]

        with tempfile.TemporaryDirectory() as output_dir:
            # Loop twice so that we exercise the buffering behavior of this function as well - the second time through,
            # the requested file will already exist due to the first call, and a shortcut skipping downloading should
            # be invoked. It's difficult to verify that this occurs from the caller's perspective, but it can be verified
            # in code coverage.
            for _ in range(2):
                result = diyepw.create_amy_epw_files_for_years_and_wmos(
                    years=years,
                    wmo_indices=wmo_indices,
                    max_records_to_interpolate=2,
                    max_records_to_impute=50,
                    max_missing_amy_rows=10,
                    allow_downloads=True,
                    amy_epw_dir=output_dir
                )
                self.assertEqual(list(result.keys()), years)

                for year in result:
                    self.assertEqual(list(result[year].keys()), wmo_indices)

                    for wmo_index in result[year]:
                        for file_path in result[year][wmo_index]:
                            self._validate_epw_file(file_path)

    def _validate_epw_file(self, file_path):
        """Validate that a given file is a valid EPW file"""

        # Verify that the generated file can be parsed as an EPW
        with open(file_path, "r") as m:
            try:
                parsed_epw, col_names = pvlib.iotools.parse_epw(m)
            except Exception as e:
                raise Exception(f"Error parsing the result of create_amy_epw_file() as an EPW file: {e}")

            # Make sure that parse_epw() actually succeeded in creating a DataFrame instance
            self.assertIsInstance(parsed_epw, pd.DataFrame)




if __name__ == '__main__': # pragma: no cover
    unittest.main()
