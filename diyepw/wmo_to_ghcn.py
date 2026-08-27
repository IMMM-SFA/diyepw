"""Resolve a 6-digit NOAA WMO index to a GHCN station identifier.

The legacy NOAA ISD-Lite product identifies stations by a 6-digit WMO index
(e.g. ``727930`` for Seattle-Tacoma Intl AP). Its replacement, GHCN-hourly
(GHCNh), uses GHCN station identifiers (e.g. ``USW00024233``) instead.

This module provides a small, self-contained mapping seeded from the NCEI
GHCNh station inventory at
``https://www.ncei.noaa.gov/oa/global-historical-climatology-network/hourly/doc/ghcnh-station-list.txt``.
The packaged mapping is built from rows in that inventory whose WMO column is
populated; non-WMO stations remain reachable only via an explicit GHCN ID.
"""

from __future__ import annotations

import os
from typing import Optional

import importlib_resources
import pandas as pd

from ._http import urlopen as _urlopen
from ._logging import _logger
from .exceptions import DownloadNotAllowedError

_INVENTORY_URL = (
    "https://www.ncei.noaa.gov/oa/global-historical-climatology-network/"
    "hourly/doc/ghcnh-station-list.txt"
)

# Fixed-width column specs documented in the GHCNh station list header.
_INVENTORY_COLSPECS = [
    (0, 11),
    (12, 20),
    (21, 30),
    (31, 37),
    (38, 40),
    (41, 71),
    (72, 75),
    (76, 79),
    (80, 86),
]
_INVENTORY_COLUMNS = [
    "ghcn_id",
    "lat",
    "lon",
    "elevation",
    "state",
    "name",
    "gsn_flag",
    "hcn_crn_flag",
    "wmo_id",
]


def _default_map_path() -> str:
    return str(importlib_resources.files("diyepw") / "data/ghcn_station_map.csv")


def _load_map(map_path: Optional[str] = None) -> pd.DataFrame:
    path = map_path or _default_map_path()
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"GHCN station map not found at {path}. Pass allow_downloads=True to "
            "wmo_to_ghcn_id() to (re)build it from NCEI."
        )
    return pd.read_csv(path, dtype={"wmo_index": int, "ghcn_id": str})


def _build_map_from_inventory(map_path: str) -> pd.DataFrame:
    _logger.info(f"Downloading GHCNh station inventory from {_INVENTORY_URL}")
    with _urlopen(_INVENTORY_URL) as response:
        df = pd.read_fwf(
            response,
            colspecs=_INVENTORY_COLSPECS,
            names=_INVENTORY_COLUMNS,
            dtype=str,
        )

    df["wmo_id"] = df["wmo_id"].astype(str).str.strip()
    df["ghcn_id"] = df["ghcn_id"].astype(str).str.strip()
    df["name"] = df["name"].astype(str).str.strip()

    with_wmo = df[df["wmo_id"].str.match(r"^\d{5}$", na=False)].copy()
    # ISD-Lite uses the 5-digit WMO number with a trailing 0 appended.
    with_wmo["wmo_index"] = with_wmo["wmo_id"].astype(int) * 10
    out = (
        with_wmo[["wmo_index", "ghcn_id", "name"]]
        .sort_values("wmo_index")
        .drop_duplicates(subset=["wmo_index"])
        .reset_index(drop=True)
    )
    out.to_csv(map_path, index=False)
    _logger.info(f"Wrote {len(out)} WMO-to-GHCN entries to {map_path}")
    return out


def wmo_to_ghcn_id(
    wmo_index: int,
    *,
    allow_downloads: bool = False,
    map_path: Optional[str] = None,
) -> str:
    """Return the GHCN station identifier for a 6-digit ISD-Lite WMO index.

    :param wmo_index: 6-digit WMO index (e.g. ``727930``).
    :param allow_downloads: If True and the packaged map is missing, the NCEI
        GHCNh station inventory will be downloaded and parsed.
    :param map_path: Optional override for the CSV mapping file location.
    :raises LookupError: If no GHCN station corresponds to ``wmo_index``.
    """
    path = map_path or _default_map_path()
    try:
        df = _load_map(path)
    except FileNotFoundError:
        if not allow_downloads:
            raise DownloadNotAllowedError(
                f"GHCN station map {path} is not present and downloads are not allowed. "
                "Re-run with allow_downloads=True."
            )
        df = _build_map_from_inventory(path)

    matches = df.loc[df["wmo_index"] == int(wmo_index), "ghcn_id"]
    if matches.empty:
        raise LookupError(
            f"No GHCN station ID found for WMO index {wmo_index}. Provide a GHCN "
            "station ID explicitly via the station_id argument."
        )
    return str(matches.iloc[0])
