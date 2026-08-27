"""Unit tests for leap-year handling in analyze_amy_file."""

import os
import tempfile
import unittest

import diyepw

GHCNH_HEADER = (
    "STATION|Station_name|DATE|Year|Month|Day|Hour|Minute|LATITUDE|LONGITUDE|"
    "ELEVATION|temperature|dew_point_temperature|sea_level_pressure|wind_direction|wind_speed"
)
GHCNH_ROW = (
    "USW00094846|CHICAGO OHARE INTL AP|{date}|2024|1|1|0|0|41.96|-87.93|"
    "204.8|16.9|2.5|1019.9|180|1.4"
)


class AnalyzeAmyFileLeapYearTest(unittest.TestCase):
    def test_isd_lite_leap_year_inferred_from_data(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "one_row")
            with open(path, "w") as fh:
                fh.write("2024 01 01 01   194   139 10200    80    15     0     0 -9999\n")
            analysis = diyepw.analyze_noaa_isd_lite_file(path)
            self.assertEqual(analysis["total_rows_missing"], 8783)

    def test_isd_lite_explicit_year_overrides_inference(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "one_row")
            with open(path, "w") as fh:
                fh.write("2018 01 01 01   194   139 10200    80    15     0     0 -9999\n")
            analysis = diyepw.analyze_noaa_isd_lite_file(path, year=2024)
            self.assertEqual(analysis["total_rows_missing"], 8783)

    def test_ghcnh_leap_year_inferred_from_data(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "fixture.psv")
            with open(path, "w") as fh:
                fh.write(GHCNH_HEADER + "\n")
                fh.write(GHCNH_ROW.format(date="2024-01-01T00:00:00") + "\n")
            analysis = diyepw.analyze_amy_file(path)
            self.assertEqual(analysis["total_rows_missing"], 8783)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
