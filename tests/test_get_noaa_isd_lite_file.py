import unittest
import diyepw
import pkg_resources
import tempfile
import os


class TmyGetNoaaIsdLiteFileTest(unittest.TestCase):
    """
    Tests of the behavior of the get_noaa_isd_lite_file() function
    """

    def test_file_download(self):
        """
        Confirm the function works correctly if all files (the catalog and the file itself) must be downloaded.
        """
        with tempfile.TemporaryDirectory() as output_dir:
            wmo_index = 722016
            year = 2015

            # If we don't pass the allow_downloads flag to give explicit permission, the function should recognize that
            # the requested file is not present in output_dir (which is empty) and raise an Exception rather than proceed
            with self.assertRaises(Exception):
                diyepw.get_noaa_isd_lite_file(wmo_index, year, output_dir=output_dir)

            # Now pass the allow_downloads flag and check that the download behavior works correctly.
            # Call the method twice to exercise the shortcut in the code that will skip the download if
            # the file is already present in output_dir. This is difficult to confirm (unless we wanted to verify
            # that the second call ran faster?) but can be verified by seeing in the coverage report that the
            # code branch associated with that behavior has been invoked.
            for _ in range(2):
                file = diyepw.get_noaa_isd_lite_file(wmo_index, year, output_dir=output_dir, allow_downloads=True)
                self._validate_isd_lite_file(file)

        # We need a new temp directory because we need to trigger another download attempt
        with tempfile.TemporaryDirectory() as output_dir:
            # Delete the catalog data file, so that the next call to get_tmy_epw_file() will be forced to trigger
            # the file to be downloaded anew
            os.unlink(pkg_resources.resource_filename("diyepw", f"data/noaa_isd_lite_catalogs/{year}"))

            # With the catalog missing and a fresh temporary output directory, we get the same behavior as above
            # when trying to get a TMY EPW file without passing allow_downloads, but in this case it is due to
            # the catalog failing to download.
            with self.assertRaises(Exception):
                diyepw.get_noaa_isd_lite_file(wmo_index, year, output_dir=output_dir)

            # Now call it with allow_downloads to ensure that the catalog downloads correctly. Here we
            # don't have to do two calls as we did above because the "catalog already exists" shortcut
            # will have been exercised by at least one of the two calls in the above loop, if not both.
            file = diyepw.get_noaa_isd_lite_file(wmo_index, year, output_dir=output_dir, allow_downloads=True)
            self._validate_isd_lite_file(file)

    def _validate_isd_lite_file(self, file_path:str):
        """Perform some assertions on a file to verify that it is a valid ISD Lite file"""

        # analyze_noaa_isd_lite_file() interacts with the contents of a file deeply enough
        # to serve as a good approximation for validating that the file is well-formatted,
        # since the function will raise an Exception if it's unable to read data from the
        # file due to it being incorrectly formatted.
        analysis = diyepw.analyze_noaa_isd_lite_file(file_path)
        for field_name in ['file', 'total_rows_missing', 'max_consec_rows_missing']:
            self.assertIn(field_name, analysis)
        self.assertEqual(analysis['file'], file_path)

if __name__ == '__main__': # pragma: no cover
    unittest.main()
