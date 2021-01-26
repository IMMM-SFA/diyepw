import unittest
import diyepw
import pkg_resources
import tempfile
import os


class TmyGetEpwFileTest(unittest.TestCase):
    """
    Tests of the behavior of the get_tmy_epw_file function
    """

    def test_file_download(self):
        """
        Confirm the function works correctly if all files (the catalog and the file itself) must be downloaded.
        """
        with tempfile.TemporaryDirectory() as output_dir:
            wmo_index = 722016

            # If we don't pass the allow_downloads flag to give explicit permission, the function should recognize that
            # the requested file is not present in output_dir (which is empty) and raise an Exception rather than proceed
            with self.assertRaises(Exception):
                diyepw.get_tmy_epw_file(wmo_index, output_dir=output_dir)

            # Now pass the allow_downloads flag and check that the download behavior works correctly
            # We parse the downloaded file into a Meteorology instance. Just the fact that this succeeds without
            # error is a good indication that the download functioned correctly; we just assert that the class
            # instantiated successfully and that it parsed the expected WMO Index out of the downloaded file
            # to ensure that it seems to have worked as expected
            file_path = diyepw.get_tmy_epw_file(wmo_index, output_dir=output_dir, allow_downloads=True)
            meteorology = diyepw.Meteorology.from_tmy3_file(file_path)
            self.assertIsInstance(meteorology, diyepw.Meteorology)
            self.assertEqual(meteorology.station_number, wmo_index)

            # Call the same method again to exercise the shortcut in the code that will skip the download if
            # the file is already present in output_dir. This is difficult to confirm (unless we wanted to verify
            # that the second call ran faster?) but can be verified by seeing in the coverage report that the
            # code branch associated with that behavior has been invoked.
            diyepw.get_tmy_epw_file(wmo_index, output_dir=output_dir, allow_downloads=True)

        # We need a new temp directory because we need to trigger another download attempt
        with tempfile.TemporaryDirectory() as output_dir:
            # Delete the catalog data file, so that the next call to get_tmy_epw_file() will be forced to trigger
            # the file to be downloaded anew
            os.unlink(pkg_resources.resource_filename("diyepw", "data/tmy_epw_catalogs/tmy_epw_catalog.csv"))

            # With the catalog missing and a fresh temporary output directory, we get the same behavior as above
            # when trying to get a TMY EPW file without passing allow_downloads, but in this case it is due to
            # the catalog failing to download.
            with self.assertRaises(Exception):
                diyepw.get_tmy_epw_file(wmo_index, output_dir=output_dir)

            # Now call it with allow_downloads to ensure that the catalog downloads correctly
            file_path = diyepw.get_tmy_epw_file(wmo_index, output_dir=output_dir, allow_downloads=True)
            meteorology = diyepw.Meteorology.from_tmy3_file(file_path)
            self.assertIsInstance(meteorology, diyepw.Meteorology)
            self.assertEqual(meteorology.station_number, wmo_index)

    def test_argument_validation(self):
        """
        Ensure that the get_tmy_epw_file() method correctly handles invalid arguments
        """

        invalid_args = [
            { "wmo_index": "banana" }, # Invalid WMO index
            { "wmo_index": "777777" }, # Nonexistent WMO index
            { "wmo_index": "722016", 'output_dir': '08jtounaksnfehurousoejfowijf' } # Nonexistent output directory
        ]

        for args in invalid_args:
            with self.assertRaises(Exception):
                diyepw.get_tmy_epw_file(**args)

if __name__ == '__main__': # pragma: no cover
    unittest.main()
