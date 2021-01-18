import unittest
import diyepw
import pkg_resources


class AnalyzeNoaaIsdLiteFileTest(unittest.TestCase):
    """
    Tests of the behavior of the analyze_noaa_isd_lite_file function
    """

    def test_file_without_missing_rows(self):
        """
        Confirm the correct behavior of the script when handling an ISD Lite file that has no missing rows
        :return:
        """
        isd_lite_file = pkg_resources.resource_filename(
            'diyepw',
            'test/files/noaa_isd_lite/uncompressed_no_missing_rows'
        )

        analysis = diyepw.analyze_noaa_isd_lite_file(isd_lite_file)
        self._assert_analysis_for_no_missing_rows(analysis, isd_lite_file)

    def test_compression_methods(self):
        """
        Confirm that the "compression" argument can be used to force decompression from a given format
        even if the file has no extension, and that the default "infer" method works correctly to
        decompress a file.
        :return:
        """

        # Test that manually setting a compression argument works as expected
        zip_file_path = pkg_resources.resource_filename(
            'diyepw',
            'test/files/noaa_isd_lite/zip_no_extension_no_missing_rows'
        )
        analysis = diyepw.analyze_noaa_isd_lite_file(zip_file_path, compression='zip')
        self._assert_analysis_for_no_missing_rows(analysis, zip_file_path)

        # Test that the default "inferred" behavior works correctly for a format other than the
        # default GZIP that is otherwise used in all our tests and scripts
        bz2_file_path = pkg_resources.resource_filename(
            'diyepw',
            'test/files/noaa_isd_lite/no_missing_rows.bz2'
        )
        analysis = diyepw.analyze_noaa_isd_lite_file(bz2_file_path)
        self._assert_analysis_for_no_missing_rows(analysis, bz2_file_path)

    def _assert_analysis_for_no_missing_rows(self, analysis:dict, file_name:str):
        self.assertEqual(analysis['file'], file_name)
        self.assertEqual(analysis['total_rows_missing'], 0)
        self.assertEqual(analysis['max_consec_rows_missing'], 0)