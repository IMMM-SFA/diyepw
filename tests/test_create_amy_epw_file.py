import unittest
import diyepw
import tempfile
import pvlib
import pandas as pd
import os

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class TmyCreateAmyEpwFileTest(unittest.TestCase):
    """
    Tests of the behavior of the create_amy_epw_file function
    """

    def test_file_creation_with_download(self):
        """Verify the standard use case - a new file that is not already available being requested with
           downloads enabled"""

        # Loop twice so that we exercise the buffering behavior of this function as well - the second time through,
        # the requested file will already exist due to the first call, and a shortcut skipping downloading should
        # be invoked. It's difficult to verify that this occurs from the caller's perspective, but it can be verified
        # in code coverage.
        for _ in range(2):
            file_path = diyepw.create_amy_epw_file(
                702910,
                2018,
                max_records_to_interpolate=5,
                max_records_to_impute=40,
                allow_downloads=True
            )
            self._validate_epw_file(file_path)

    def test_file_creation_with_amy_files(self):
        """Test the use case that the caller specifies AMY files to be used instead of allowing these
           to be determined automatically"""
        file_path = diyepw.create_amy_epw_file(
            725300,
            2017,
            max_records_to_interpolate=2, # Intentionally very low so that imputation code gets exercised
            max_records_to_impute=20,
            allow_downloads=True,
            amy_files = (
                os.path.join(THIS_DIR, 'files', 'noaa_isd_lite', '725300-2017.gz'),
                os.path.join(THIS_DIR, 'files', 'noaa_isd_lite', '725300-2018.gz')
            )
        )
        self._validate_epw_file(file_path)

    def test_leap_year(self):
        """Test that an AMY EPW file can be generated for a leap year, which is an issue because the
           TMY files we use have the number of hours for a non-leap year, which causes size mismatches
           when mapping AMY data onto the TMY EPW file without special handling"""
        file_path = diyepw.create_amy_epw_file(
            725300,
            2016,
            max_records_to_interpolate=2,
            max_records_to_impute=20,
            allow_downloads=True,
            amy_files = (
                os.path.join(THIS_DIR, 'files', 'noaa_isd_lite', '725300-2016.gz'),
                os.path.join(THIS_DIR, 'files', 'noaa_isd_lite', '725300-2017.gz')
            )
        )
        self._validate_epw_file(file_path)

    def test_validation_errors(self):
        """Verify that invalid inputs result in errors as expected"""

        # It should not be possible to pass both amy_dir and amy_files, since both define which AMY files should
        # be used to handle the call.
        with self.assertRaises(Exception):
            diyepw.create_amy_epw_file(
                724940,
                2018,
                max_records_to_interpolate=5,
                max_records_to_impute=20,
                amy_dir="some_dir",
                amy_files=("some_file", "some_other_file")
            )

        # If amy_files is used to define the current and next year AMY input files, then
        # an Exception should be raised if either of the two is not a real file. We create
        # a temporary file so that one of the paths does exist and pass a dummy for the other.
        with tempfile.NamedTemporaryFile('r') as tmp_file:
            with self.assertRaises(Exception):
                diyepw.create_amy_epw_file(
                    724940,
                    2018,
                    max_records_to_interpolate=5,
                    max_records_to_impute=20,
                    amy_files=(tmp_file.name, "some_other_file")
                )
            with self.assertRaises(Exception):
                diyepw.create_amy_epw_file(
                    724940,
                    2018,
                    max_records_to_interpolate=5,
                    max_records_to_impute=20,
                    amy_files=("some_file", tmp_file.name)
                )

        # An otherwise valid call, passed inputs into which we have injected values that would result in an invalid EPW
        # file being generated, should result in an exception
        with self.assertRaises(Exception):
            with tempfile.TemporaryDirectory() as tmp_dir:
                diyepw.create_amy_epw_file(
                    725300,
                    2017,
                    max_records_to_interpolate=5,
                    max_records_to_impute=20,
                    amy_epw_dir=tmp_dir,
                    allow_downloads=True,
                    amy_files = (
                        os.path.join(THIS_DIR, 'files', 'noaa_isd_lite', '725300-2017_epw_violations.gz'),
                        os.path.join(THIS_DIR, 'files', 'noaa_isd_lite', '725300-2018.gz')
                    )
                )

        # We should get an exception if we specify maximum numbers of missing or consecutive missing AMY input rows
        # that are less than the number of missing rows in our AMY input files
        with self.assertRaises(Exception):
            with tempfile.TemporaryDirectory() as tmp_dir:
                diyepw.create_amy_epw_file(
                    725300,
                    2017,
                    max_records_to_interpolate=5,
                    max_records_to_impute=20,
                    amy_epw_dir=tmp_dir,
                    max_missing_amy_rows=15,
                    amy_files = (
                        os.path.join(THIS_DIR, 'files', 'noaa_isd_lite', 'only_one_row'),
                        os.path.join(THIS_DIR, 'files', 'noaa_isd_lite', '725300-2018.gz')
                    )
                )

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
