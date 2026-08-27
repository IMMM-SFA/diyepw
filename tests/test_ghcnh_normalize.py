"""Unit tests for GHCNh normalization, in particular sentinel-value handling."""

import os
import tempfile
import unittest

from diyepw._ghcnh_normalize import read_ghcnh_psv

HEADER = (
    "STATION|Station_name|DATE|Year|Month|Day|Hour|Minute|LATITUDE|LONGITUDE|"
    "ELEVATION|temperature|dew_point_temperature|sea_level_pressure|wind_direction|wind_speed"
)


def _row(date: str, wind_direction) -> str:
    return (
        f"USW00094846|CHICAGO OHARE INTL AP|{date}|2017|1|1|0|0|41.96|-87.93|"
        f"204.8|16.9|2.5|1019.9|{wind_direction}|1.4"
    )


class ReadGhcnhPsvWindDirectionTest(unittest.TestCase):
    def _read(self, rows):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "fixture.psv")
            with open(path, "w") as fh:
                fh.write(HEADER + "\n")
                fh.write("\n".join(rows) + "\n")
            return read_ghcnh_psv(path)

    def test_wind_direction_sentinel_normalizes_to_nan(self):
        df = self._read([_row("2017-01-01T00:00:00", 999)])
        self.assertTrue(df["Wind_Direction"].isna().iloc[0])

    def test_wind_direction_boundary_values_are_preserved(self):
        df = self._read([
            _row("2017-01-01T00:00:00", 0),
            _row("2017-01-01T01:00:00", 360),
            _row("2017-01-01T02:00:00", 180),
        ])
        self.assertEqual(list(df["Wind_Direction"]), [0.0, 360.0, 180.0])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
