"""Analyze AMY observation files (ISD-Lite or GHCN-hourly) for AMY EPW suitability.

This module supersedes the original :mod:`diyepw.analyze_noaa_isd_lite_file`
module but the latter continues to re-export :func:`analyze_noaa_isd_lite_file`
for backward compatibility.
"""

from __future__ import annotations

import os
from calendar import isleap
from typing import Literal, Optional

import numpy as np
import pandas as pd

from ._ghcnh_normalize import (
    GHCNH_CANONICAL_COLUMNS,
    collapse_to_hourly,
    read_ghcnh_psv,
)

_AMY_FORMATS = ("auto", "isd_lite", "ghcnh")


def _hours_in_year(timestamps: pd.Series, year: Optional[int]) -> int:
    """Number of UTC hours in a calendar year (8760, or 8784 in a leap year).

    Uses ``year`` when given; otherwise infers it from the first non-null
    timestamp observed in the file, falling back to 8760 only if the file
    has no usable timestamps at all to infer from.
    """
    if year is None:
        first_valid = timestamps.dropna()
        year = first_valid.iloc[0].year if not first_valid.empty else None
    return 8784 if year is not None and isleap(year) else 8760


def _detect_format(file: str) -> str:
    lowered = file.lower()
    if lowered.endswith(".psv"):
        return "ghcnh"
    return "isd_lite"


def _analyze_isd_lite_file(file: str, compression: str = "infer", year: Optional[int] = None) -> dict:
    df = pd.read_csv(
        file,
        sep=r"\s+",
        header=None,
        compression=compression,
        names=[
            "Year",
            "Month",
            "Day",
            "Hour",
            "Air_Temperature",
            "Dew_Point_Temperature",
            "Sea_Level_Pressure",
            "Wind_Direction",
            "Wind_Speed_Rate",
            "Sky_Condition_Total_Coverage_Code",
            "Liquid_Precipitation_Depth_Dimension_1H",
            "Liquid_Precipitation_Depth_Dimension_6H",
        ],
    )

    df["obs_timestamps"] = pd.to_datetime(
        pd.DataFrame(
            {
                "year": df["Year"],
                "month": df["Month"],
                "day": df["Day"],
                "hour": df["Hour"],
            }
        )
    )
    df = df.drop(columns=["Year", "Month", "Day", "Hour"])

    rows_present = df.shape[0]
    total_hours = _hours_in_year(df["obs_timestamps"], year)
    description = {
        "file": file,
        "total_rows_missing": total_hours - rows_present,
        "max_consec_rows_missing": 0,
    }
    if description["total_rows_missing"] > 0:
        description["max_consec_rows_missing"] = _max_missing_consec(
            df, "obs_timestamps", total_hours
        )
    return description


def _analyze_ghcnh_file(file: str, year: Optional[int] = None) -> dict:
    raw = read_ghcnh_psv(file)
    hourly = collapse_to_hourly(raw)
    # Convert -9999 sentinels in raw data (some legacy sources still pass through)
    hourly = hourly.replace(-9999, np.nan)
    populated = hourly.dropna(how="all")
    rows_present = populated.shape[0]
    total_hours = _hours_in_year(populated.index.to_series(), year)
    description = {
        "file": file,
        "total_rows_missing": total_hours - rows_present,
        "max_consec_rows_missing": 0,
    }
    if description["total_rows_missing"] > 0:
        described = pd.DataFrame({"obs_timestamps": populated.index})
        description["max_consec_rows_missing"] = _max_missing_consec(
            described, "obs_timestamps", total_hours
        )
    return description


def _max_missing_consec(df: pd.DataFrame, timestamp_col_name: str, total_hours: int = 8760) -> int:
    if df.empty:
        return total_hours
    all_timestamps = pd.date_range(df[timestamp_col_name].iloc[0], periods=total_hours, freq="h")
    all_times = pd.DataFrame(all_timestamps, columns=["all_timestamps"])
    df_all_times = pd.merge(
        all_times, df, how="left", left_on="all_timestamps", right_on=timestamp_col_name
    )
    missing_times = df_all_times[df_all_times.isnull().any(axis=1)]["all_timestamps"]
    if missing_times.empty:  # pragma: no cover
        return 0
    missing_times_diff = missing_times.diff()
    counter = 1
    max_missing_rows = 1
    for step in missing_times_diff:
        if step == pd.Timedelta("1h"):
            counter += 1
            if counter > max_missing_rows:
                max_missing_rows = counter
        elif step > pd.Timedelta("1h"):
            counter = 1
    return max_missing_rows


def analyze_amy_file(
    file: str,
    *,
    format: Literal["auto", "isd_lite", "ghcnh"] = "auto",
    compression: str = "infer",
    year: Optional[int] = None,
) -> dict:
    """Analyze an AMY observation file for AMY EPW suitability.

    :param file: Path to the file. Supported formats are NOAA ISD-Lite (whitespace
        delimited, with extensions ``.gz``/``.csv``) and NCEI GHCN-hourly PSV
        files (``.psv``).
    :param format: ``"auto"`` (default), ``"isd_lite"``, or ``"ghcnh"``.
    :param compression: ``compression`` argument forwarded to ``pandas.read_csv``
        when reading ISD-Lite files.
    :param year: The calendar year the file represents, used to determine whether
        it should contain 8760 or 8784 (leap year) hourly rows. If omitted, the
        year is inferred from the file's own timestamps.
    :return: ``{"file", "total_rows_missing", "max_consec_rows_missing"}``.
    """
    if format not in _AMY_FORMATS:
        raise ValueError(f"format must be one of {_AMY_FORMATS}, got {format!r}")

    file = os.fspath(file)
    resolved = _detect_format(file) if format == "auto" else format

    if resolved == "ghcnh":
        return _analyze_ghcnh_file(file, year=year)
    return _analyze_isd_lite_file(file, compression=compression, year=year)
