"""Download yearly GHCN-hourly (GHCNh) PSV files from NCEI.

GHCNh is NCEI's replacement for the legacy ISD-Lite product. Yearly per-station
PSV files are published under the NCEI object store at:

    ``https://www.ncei.noaa.gov/oa/global-historical-climatology-network/
    hourly/access/by-year/<YEAR>/psv/GHCNh_<GHCN_ID>_<YEAR>.psv``

If the object-store URL is unavailable, this module falls back to the NCEI
Access Data Service REST API (``dataset=global-hourly``).
"""

from __future__ import annotations

import os
from typing import Optional
from urllib.error import HTTPError, URLError

import importlib_resources

from ._http import urlopen as _urlopen
from ._logging import _logger
from .exceptions import DownloadNotAllowedError

_OBJECT_STORE_URL_TEMPLATE = (
    "https://www.ncei.noaa.gov/oa/global-historical-climatology-network/"
    "hourly/access/by-year/{year}/psv/GHCNh_{ghcn_id}_{year}.psv"
)

# NCEI Access Data Service can serve GHCNh as CSV via the global-hourly dataset.
_ACCESS_API_TEMPLATE = (
    "https://www.ncei.noaa.gov/access/services/data/v1"
    "?dataset=global-hourly&stations={ghcn_id}"
    "&startDate={year}-01-01&endDate={year}-12-31&format=csv"
    "&includeAttributes=false&includeStationName=true&includeStationLocation=true"
)


def _ghcnh_object_store_url(ghcn_id: str, year: int) -> str:
    return _OBJECT_STORE_URL_TEMPLATE.format(year=year, ghcn_id=ghcn_id)


def _ghcnh_access_api_url(ghcn_id: str, year: int) -> str:
    return _ACCESS_API_TEMPLATE.format(year=year, ghcn_id=ghcn_id)


def get_ghcnh_file(
    station_id: str,
    year: int,
    *,
    output_dir: Optional[str] = None,
    allow_downloads: bool = False,
) -> str:
    """Return the local path to a yearly GHCNh PSV file.

    :param station_id: GHCN station identifier (e.g. ``USW00024233``).
    :param year: The calendar year of the file.
    :param output_dir: Directory in which the PSV should be saved/looked up.
        If a file matching the station/year is already present, no download
        is performed.
    :param allow_downloads: If True, missing files will be downloaded from
        NCEI. If False and the file is not already present, a
        :class:`DownloadNotAllowedError` is raised.
    """
    if not isinstance(station_id, str) or not station_id:
        raise ValueError("station_id must be a non-empty string GHCN station identifier")

    if output_dir is None:  # pragma: no cover
        output_dir = str(importlib_resources.files("diyepw") / "data/ghcnh_files")
        _logger.info(
            f"get_ghcnh_file() - output_dir was not defined, will use {output_dir}"
        )

    if not os.path.exists(output_dir):  # pragma: no cover
        os.makedirs(output_dir, exist_ok=True)
        _logger.info(
            f"get_ghcnh_file() - {output_dir} did not exist, so has been created"
        )

    file_name = f"GHCNh_{station_id}_{year}.psv"
    file_path = os.path.join(output_dir, file_name)

    if os.path.exists(file_path):
        return file_path

    object_store_url = _ghcnh_object_store_url(station_id, year)
    api_url = _ghcnh_access_api_url(station_id, year)

    if not allow_downloads:
        raise DownloadNotAllowedError(
            f"The GHCNh file {file_path} is not present. Pass allow_downloads=True "
            f"to allow the missing data to be automatically downloaded from "
            f"{object_store_url}"
        )

    last_error: Optional[Exception] = None
    for source_label, url in (("object store", object_store_url), ("access API", api_url)):
        try:
            with _urlopen(url) as response:
                payload = response.read()
            with open(file_path, "wb") as downloaded_file:
                downloaded_file.write(payload)
            _logger.info(
                f"Downloaded GHCNh {station_id}/{year} via {source_label} ({url})"
            )
            return file_path
        except HTTPError as exc:
            last_error = exc
            _logger.info(
                f"GHCNh {source_label} returned HTTP {exc.code} for {url}; "
                "trying next source"
            )
            continue
        except URLError as exc:  # pragma: no cover - network-dependent
            last_error = exc
            _logger.info(
                f"GHCNh {source_label} URL error for {url}: {exc.reason}; "
                "trying next source"
            )
            continue

    raise Exception(
        f"Failed to download GHCNh data for station {station_id} year {year}. "
        f"Last error: {last_error}"
    )
