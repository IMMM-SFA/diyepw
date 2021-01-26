import unittest
import diyepw
import os

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class AnalyzeNoaaIsdLiteFileTest(unittest.TestCase):
    """
    Tests of the behavior of the analyze_noaa_isd_lite_file function
    """

    def test_file_without_missing_rows(self):
        """
        Confirm the correct behavior of the script when handling an ISD Lite file that has no missing rows
        """
        isd_lite_file = os.path.join(THIS_DIR, 'files', 'noaa_isd_lite', 'uncompressed_no_missing_rows')

        analysis = diyepw.analyze_noaa_isd_lite_file(isd_lite_file)
        self._assert_analysis_for_no_missing_rows(analysis, isd_lite_file)

    def test_compression_methods(self):
        """
        Confirm that the "compression" argument can be used to force decompression from a given format
        even if the file has no extension, and that the default "infer" method works correctly to
        decompress a file.
        """

        # Test that manually setting a compression argument works as expected
        zip_file_path = os.path.join(THIS_DIR, 'files', 'noaa_isd_lite', 'zip_no_extension_no_missing_rows')
        analysis = diyepw.analyze_noaa_isd_lite_file(zip_file_path, compression='zip')
        self._assert_analysis_for_no_missing_rows(analysis, zip_file_path)

        # Test that the default "inferred" behavior works correctly for a format other than the
        # default GZIP that is otherwise used in all our tests and scripts
        bz2_file_path = os.path.join(THIS_DIR, 'files', 'noaa_isd_lite', 'no_missing_rows.bz2')
        analysis = diyepw.analyze_noaa_isd_lite_file(bz2_file_path)
        self._assert_analysis_for_no_missing_rows(analysis, bz2_file_path)

    def test_many_missing_rows(self):
        """
        Confirm correct behavior when too many rows are missing from a file. For this test we
        use a file that has only a single row defined.
        """
        file_path = os.path.join(THIS_DIR, 'files', 'noaa_isd_lite', 'only_one_row')
        analysis = diyepw.analyze_noaa_isd_lite_file(file_path)
        self.assertEqual(analysis['total_rows_missing'], 8759)
        self.assertEqual(analysis['max_consec_rows_missing'], 8759)

    def test_consecutive_rows(self):
        """
        Confirm that the correct number of consecutive missing rows is found in a file with sections
        of missing rows of various lengths. For this test we use a file that has lots of rows deleted,
        but the largest sequential chunk of missing rows is 17 hours long
        """
        file_path = os.path.join(THIS_DIR, 'files', 'noaa_isd_lite', 'max_17_missing_rows')
        analysis = diyepw.analyze_noaa_isd_lite_file(file_path)
        self.assertEqual(analysis['max_consec_rows_missing'], 17)

    def _assert_analysis_for_no_missing_rows(self, analysis:dict, file_name:str):
        self.assertEqual(analysis['file'], file_name)
        self.assertEqual(analysis['total_rows_missing'], 0)
        self.assertEqual(analysis['max_consec_rows_missing'], 0)


if __name__ == '__main__': # pragma: no cover
    unittest.main()
