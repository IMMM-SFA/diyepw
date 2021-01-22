import unittest
import diyepw
import pkg_resources


class AnalyzeNoaaIsdLiteFilesTest(unittest.TestCase):
    """
    Tests of the behavior of the analyze_noaa_isd_lite_files function
    """

    def test_files(self):
        """
        Confirm the correct behavior of the script when handling our set of test ISD Lite files
        """
        file_paths = map(
            lambda file_name: pkg_resources.resource_filename('diyepw', 'test/files/noaa_isd_lite/' + file_name),
            [
                'max_17_missing_rows',
                'no_missing_rows.bz2',
                'only_one_row',
                'uncompressed_no_missing_rows'
            ]
        )

        analysis = diyepw.analyze_noaa_isd_lite_files(
            file_paths,
            max_missing_rows = 60,
            max_consecutive_missing_rows = 16
        )

        # The two files with no missing rows should be labeled as "good", the one with 17 missing rows should be
        # labeled as "too many consecutive rows missing", and the remaining file, which has only a single row, should
        # be labeled as "too many total rows missing" because that category is given priority over "too many consecutive"
        self.assertEqual(len(analysis['good']), 2)
        for good_res in analysis['good']:
            self.assertEqual(good_res['total_rows_missing'], 0)
            self.assertEqual(good_res['max_consec_rows_missing'], 0)

        self.assertEqual(len(analysis['too_many_total_rows_missing']), 1)
        self.assertEqual(analysis['too_many_total_rows_missing'][0]['total_rows_missing'], 8759)
        self.assertEqual(analysis['too_many_total_rows_missing'][0]['max_consec_rows_missing'], 8759)

        self.assertEqual(len(analysis['too_many_consecutive_rows_missing']), 1)
        self.assertEqual(analysis['too_many_consecutive_rows_missing'][0]['total_rows_missing'], 59)
        self.assertEqual(analysis['too_many_consecutive_rows_missing'][0]['max_consec_rows_missing'], 17)
