"""Unit tests for the GHCN-hourly downloader."""

import importlib
import io
import os
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

import diyepw
from diyepw import get_ghcnh_file
from diyepw.exceptions import DownloadNotAllowedError

# `diyepw.__init__` re-exports the `get_ghcnh_file` function with the same name as the
# submodule, which shadows the submodule attribute. Use importlib to retrieve the actual
# module object for patching its internal `_urlopen` symbol.
ghcnh_module = importlib.import_module("diyepw.get_ghcnh_file")

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(THIS_DIR, "files", "ghcnh", "GHCNh_USW00094846_2017.psv")


class _FakeResponse:
    def __init__(self, payload: bytes):
        self._stream = io.BytesIO(payload)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self._stream.close()

    def read(self):
        return self._stream.read()


class GetGhcnhFileTest(unittest.TestCase):
    def test_disallowed_download_raises(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaises(DownloadNotAllowedError):
                get_ghcnh_file("USW00094846", 2017, output_dir=tmp_dir, allow_downloads=False)

    def test_object_store_path_used_first(self):
        with open(FIXTURE, "rb") as fh:
            payload = fh.read()

        calls = []

        def fake_urlopen(url):
            calls.append(url)
            return _FakeResponse(payload)

        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch.object(ghcnh_module, "_urlopen", side_effect=fake_urlopen):
                path = get_ghcnh_file(
                    "USW00094846", 2017, output_dir=tmp_dir, allow_downloads=True
                )
            self.assertTrue(os.path.exists(path))
            self.assertTrue(calls[0].endswith("GHCNh_USW00094846_2017.psv"))
            self.assertEqual(len(calls), 1)

    def test_falls_back_to_access_api_on_404(self):
        with open(FIXTURE, "rb") as fh:
            payload = fh.read()

        def fake_urlopen(url):
            if "by-year" in url:
                raise HTTPError(url, 404, "Not Found", hdrs=None, fp=None)
            return _FakeResponse(payload)

        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch.object(ghcnh_module, "_urlopen", side_effect=fake_urlopen):
                path = get_ghcnh_file(
                    "USW00094846", 2017, output_dir=tmp_dir, allow_downloads=True
                )
            self.assertTrue(os.path.exists(path))

    def test_already_present_file_is_reused(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            existing = os.path.join(tmp_dir, "GHCNh_USW00094846_2017.psv")
            with open(existing, "w") as fh:
                fh.write("placeholder")
            with patch.object(ghcnh_module, "_urlopen") as urlopen_mock:
                path = get_ghcnh_file(
                    "USW00094846", 2017, output_dir=tmp_dir, allow_downloads=True
                )
            urlopen_mock.assert_not_called()
            self.assertEqual(path, existing)


class WmoToGhcnIdTest(unittest.TestCase):
    def test_known_station(self):
        self.assertEqual(diyepw.wmo_to_ghcn_id(727930), "USW00024233")
        self.assertEqual(diyepw.wmo_to_ghcn_id(725300), "USW00094846")

    def test_unknown_station_raises_lookup_error(self):
        with self.assertRaises(LookupError):
            diyepw.wmo_to_ghcn_id(999999)


class AnalyzeAmyFileGhcnhTest(unittest.TestCase):
    def test_ghcnh_analyzer_detects_full_year(self):
        analysis = diyepw.analyze_amy_file(FIXTURE)
        self.assertEqual(analysis["total_rows_missing"], 0)

    def test_isd_lite_still_handled_via_shim(self):
        isd_path = os.path.join(THIS_DIR, "files", "noaa_isd_lite", "725300-2017.gz")
        analysis = diyepw.analyze_noaa_isd_lite_file(isd_path)
        self.assertIn("total_rows_missing", analysis)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
