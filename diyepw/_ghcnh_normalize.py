"""Convert GHCN-hourly (GHCNh) PSV files into the canonical AMY DataFrame.

The downstream AMY pipeline in :mod:`diyepw.create_amy_epw_file` expects a
DataFrame indexed by UTC hourly timestamps with the following columns, in SI
units:

    - ``Air_Temperature`` (degrees Celsius)
    - ``Dew_Point_Temperature`` (degrees Celsius)
    - ``Sea_Level_Pressure`` (hectopascals)
    - ``Wind_Direction`` (degrees)
    - ``Wind_Speed`` (meters per second)

GHCNh files contain many observations per hour (METAR, SYNOP, remarks, etc.).
This module collapses them to a single hourly row by keeping the report whose
timestamp is closest to the top of the hour.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

GHCNH_CANONICAL_COLUMNS = [
    "Air_Temperature",
    "Dew_Point_Temperature",
    "Sea_Level_Pressure",
    "Wind_Direction",
    "Wind_Speed",
]

_GHCNH_TO_CANONICAL = {
    "temperature": "Air_Temperature",
    "dew_point_temperature": "Dew_Point_Temperature",
    "sea_level_pressure": "Sea_Level_Pressure",
    "wind_direction": "Wind_Direction",
    "wind_speed": "Wind_Speed",
}


def read_ghcnh_psv(file: str) -> pd.DataFrame:
    """Read a GHCNh PSV file, returning only the columns required for AMY."""
    usecols = ["DATE", *_GHCNH_TO_CANONICAL.keys()]
    df = pd.read_csv(
        file,
        sep="|",
        usecols=usecols,
        dtype={col: str for col in _GHCNH_TO_CANONICAL.keys()},
    )
    df = df.rename(columns=_GHCNH_TO_CANONICAL)
    df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce", utc=False)

    for col in GHCNH_CANONICAL_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # GHCNh represents a missing/variable wind direction with the sentinel value
    # 999, which is otherwise impossible since a real heading is always in
    # [0, 360]. Unlike the other canonical columns, wind direction has no
    # sentinel-free equivalent (e.g. sea level pressure can legitimately read
    # ~999 hPa), so it's sanitized by range rather than by an exact value match.
    out_of_range = (df["Wind_Direction"] < 0) | (df["Wind_Direction"] > 360)
    df.loc[out_of_range, "Wind_Direction"] = np.nan

    df.loc[df["DATE"].isna(), :] = np.nan
    df = df.dropna(subset=["DATE"]).copy()
    return df


def collapse_to_hourly(df: pd.DataFrame) -> pd.DataFrame:
    """Reduce sub-hourly GHCNh observations to one row per UTC hour.

    The row whose ``DATE`` minute/second offset is closest to the top of the hour
    is kept. The resulting DataFrame is indexed by the UTC hour as a naive
    ``datetime`` (no timezone) so that the existing AMY timezone-shift logic in
    ``create_amy_epw_file`` keeps working.
    """
    if df.empty:
        return pd.DataFrame(columns=GHCNH_CANONICAL_COLUMNS).rename_axis("timestamp")

    df = df.copy()
    floored = df["DATE"].dt.floor("h")
    delta = (df["DATE"] - floored).abs()
    df["_hour"] = floored
    df["_delta"] = delta

    df = df.sort_values(["_hour", "_delta"]).drop_duplicates(subset=["_hour"], keep="first")
    df = df.set_index("_hour").rename_axis("timestamp")
    return df[GHCNH_CANONICAL_COLUMNS]


def normalize_ghcnh_to_amy_df(raw: pd.DataFrame, *, year: int) -> pd.DataFrame:
    """Convert a parsed GHCNh DataFrame into the canonical AMY hourly DataFrame.

    The output is indexed by UTC hourly timestamps spanning the full calendar
    year ``year`` (8760/8784 hours depending on leap-year status). Missing
    observations are represented as NaN.
    """
    hourly = collapse_to_hourly(raw)

    start = pd.Timestamp(year=year, month=1, day=1, hour=0)
    end = pd.Timestamp(year=year, month=12, day=31, hour=23)
    full_index = pd.date_range(start, end, freq="h", name="timestamp")

    return hourly.reindex(full_index)


def read_and_normalize_ghcnh(file: str, *, year: int) -> pd.DataFrame:
    """Convenience wrapper combining :func:`read_ghcnh_psv` and normalization."""
    raw = read_ghcnh_psv(file)
    return normalize_ghcnh_to_amy_df(raw, year=year)


def isd_lite_canonical_from_raw(df: pd.DataFrame) -> pd.DataFrame:
    """Convert a raw ISD-Lite DataFrame to the same canonical SI schema.

    Input is the result of ``pd.read_csv(..., sep='\\s+', header=None)``, where
    ISD-Lite encodes temperature/dew point/wind speed in tenths and sea level
    pressure in hPa*10. The output uses SI units (°C, hPa, m/s, degrees) and is
    indexed by UTC hourly timestamps.
    """
    columns = [
        "Year",
        "Month",
        "Day",
        "Hour",
        "Air_Temperature",
        "Dew_Point_Temperature",
        "Sea_Level_Pressure",
        "Wind_Direction",
        "Wind_Speed",
        "Sky_Condition_Total_Coverage_Code",
        "Liquid_Precipitation_Depth_Dimension_1H",
        "Liquid_Precipitation_Depth_Dimension_6H",
    ]
    df = df.copy()
    df.columns = columns

    for col in GHCNH_CANONICAL_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df.loc[df[col] == -9999, col] = np.nan

    # ISD-Lite encodes the following in tenths.
    df["Air_Temperature"] = df["Air_Temperature"] / 10.0
    df["Dew_Point_Temperature"] = df["Dew_Point_Temperature"] / 10.0
    df["Wind_Speed"] = df["Wind_Speed"] / 10.0
    # ISD-Lite encodes SLP in hPa*10; convert to hPa.
    df["Sea_Level_Pressure"] = df["Sea_Level_Pressure"] / 10.0

    df["timestamp"] = pd.to_datetime(
        pd.DataFrame(
            {
                "year": df["Year"],
                "month": df["Month"],
                "day": df["Day"],
                "hour": df["Hour"],
            }
        )
    )
    df = df.set_index("timestamp")
    return df[GHCNH_CANONICAL_COLUMNS]
