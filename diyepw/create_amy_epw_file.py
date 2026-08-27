from .get_tmy_epw_file import get_tmy_epw_file
from .get_noaa_isd_lite_file import get_noaa_isd_lite_file
from .get_ghcnh_file import get_ghcnh_file
from .meteorology import Meteorology
from .analyze_noaa_isd_lite_file import analyze_noaa_isd_lite_file
from .wmo_to_ghcn import wmo_to_ghcn_id
from ._ghcnh_normalize import (
    GHCNH_CANONICAL_COLUMNS,
    isd_lite_canonical_from_raw,
    read_and_normalize_ghcnh,
)

import tempfile
import pandas as pd
import numpy as np
import os
import importlib_resources
from typing import Optional, Tuple
from calendar import isleap

from ._logging import _logger

_VALID_SOURCES = ("auto", "isd_lite", "ghcnh")

_tempdir_amy_epw = tempfile.mkdtemp()


def _isd_lite_placeholder_canonical_hours(
    next_calendar_year: int, n_hours: int = 23
) -> pd.DataFrame:
    """Build a canonical (SI-unit) placeholder DataFrame for the first ``n_hours``
    UTC hours of ``next_calendar_year``.

    Used when an ISD-Lite successor-year file is unavailable; the missing-value
    interpolation downstream fills in the gap.
    """
    start = pd.Timestamp(year=next_calendar_year, month=1, day=1, hour=0)
    index = pd.date_range(start, periods=n_hours, freq="h", name="timestamp")
    return pd.DataFrame(
        {col: [np.nan] * n_hours for col in GHCNH_CANONICAL_COLUMNS},
        index=index,
    )


def _read_isd_lite_raw(path: str) -> pd.DataFrame:
    return pd.read_csv(path, sep=r"\s+", header=None)


def _load_isd_lite_year_canonical(
    *,
    wmo_index: int,
    year: int,
    amy_dir: Optional[str],
    amy_files: Optional[Tuple[str, str]],
    allow_downloads: bool,
    max_missing_amy_rows: Optional[int],
):
    """Return ``(canonical_df, year_file_path)`` for ISD-Lite source.

    The DataFrame is UTC-hourly indexed (SI units) covering Jan 1 00:00 of
    ``year`` through Jan 1 22:00 of ``year+1`` (8783/8807 hours), to leave room
    for the local-timezone shift performed downstream.
    """
    if amy_files is not None:
        amy_file_path, amy_next_year_file_path = amy_files
        for p in amy_files:
            if not os.path.exists(p):
                raise Exception(f"Path {p} does not exist")
        next_raw = pd.read_csv(amy_next_year_file_path, sep=r"\s+", header=None, nrows=23)
    else:
        if amy_dir is None:
            amy_dir = str(importlib_resources.files("diyepw") / "data/noaa_isd_lite_files")
            _logger.info(
                f"No amy_dir was specified - downloaded AMY files will be stored in "
                f"the default location at {amy_dir}"
            )
        amy_file_path = get_noaa_isd_lite_file(
            wmo_index, year, output_dir=amy_dir, allow_downloads=allow_downloads
        )
        next_raw = _load_successor_year_isd_lite_raw(
            wmo_index, year + 1, amy_dir=amy_dir, allow_downloads=allow_downloads
        )

    if max_missing_amy_rows is not None:
        amy_file_analysis = analyze_noaa_isd_lite_file(amy_file_path, year=year)
        if amy_file_analysis["total_rows_missing"] > max_missing_amy_rows:
            raise _IsdLiteIncompleteError(
                amy_file_path, amy_file_analysis["total_rows_missing"], max_missing_amy_rows
            )

    year_raw = _read_isd_lite_raw(amy_file_path)
    if next_raw is None:
        canonical_next = _isd_lite_placeholder_canonical_hours(year + 1, n_hours=23)
        canonical_year = isd_lite_canonical_from_raw(year_raw)
        return pd.concat([canonical_year, canonical_next]), amy_file_path

    combined_raw = pd.concat([year_raw, next_raw]).reset_index(drop=True)
    canonical = isd_lite_canonical_from_raw(combined_raw)
    return canonical, amy_file_path


def _load_successor_year_isd_lite_raw(
    wmo_index: int,
    next_calendar_year: int,
    *,
    amy_dir: str,
    allow_downloads: bool,
    n_hours: int = 23,
):
    """Return the raw first ``n_hours`` of an ISD-Lite file for ``next_calendar_year``.

    Returns ``None`` when the file cannot be obtained and a placeholder should
    be used instead.
    """
    file_path = os.path.join(amy_dir, f"{wmo_index}-{next_calendar_year}.gz")
    if os.path.exists(file_path):
        return pd.read_csv(file_path, sep=r"\s+", header=None, nrows=n_hours)
    try:
        file_path = get_noaa_isd_lite_file(
            wmo_index, next_calendar_year, output_dir=amy_dir, allow_downloads=allow_downloads
        )
        return pd.read_csv(file_path, sep=r"\s+", header=None, nrows=n_hours)
    except Exception as exc:
        if not allow_downloads:
            raise
        _logger.warning(
            "Could not obtain NOAA ISD Lite for successor year %s (WMO %s); "
            "using placeholder UTC hours so AMY generation can proceed. Detail: %s",
            next_calendar_year,
            wmo_index,
            exc,
        )
        return None


def _load_ghcnh_year_canonical(
    *,
    station_id: str,
    year: int,
    amy_dir: Optional[str],
    amy_files: Optional[Tuple[str, str]],
    allow_downloads: bool,
):
    """Return ``(canonical_df, year_file_path)`` for GHCNh source."""
    if amy_files is not None:
        amy_file_path, amy_next_year_file_path = amy_files
        for p in amy_files:
            if not os.path.exists(p):
                raise Exception(f"Path {p} does not exist")
    else:
        if amy_dir is None:
            amy_dir = str(importlib_resources.files("diyepw") / "data/ghcnh_files")
            _logger.info(
                f"No amy_dir was specified - downloaded GHCNh files will be stored in "
                f"the default location at {amy_dir}"
            )
        amy_file_path = get_ghcnh_file(
            station_id, year, output_dir=amy_dir, allow_downloads=allow_downloads
        )
        try:
            amy_next_year_file_path = get_ghcnh_file(
                station_id,
                year + 1,
                output_dir=amy_dir,
                allow_downloads=allow_downloads,
            )
        except Exception as exc:
            _logger.warning(
                "Could not obtain GHCNh for successor year %s (station %s); "
                "using placeholder UTC hours so AMY generation can proceed. Detail: %s",
                year + 1,
                station_id,
                exc,
            )
            amy_next_year_file_path = None

    canonical_year = read_and_normalize_ghcnh(amy_file_path, year=year)
    if amy_next_year_file_path is None:
        canonical_next = _isd_lite_placeholder_canonical_hours(year + 1, n_hours=23)
    else:
        canonical_next = read_and_normalize_ghcnh(
            amy_next_year_file_path, year=year + 1
        ).iloc[:23]

    return pd.concat([canonical_year, canonical_next]), amy_file_path


class _IsdLiteIncompleteError(Exception):
    def __init__(self, file_path: str, missing: int, allowed: int):
        super().__init__(
            f"File is missing {missing} rows, but maximum allowed is {allowed}"
        )
        self.file_path = file_path
        self.missing = missing
        self.allowed = allowed


def _resolve_station_id(wmo_index: int, station_id: Optional[str], allow_downloads: bool) -> str:
    if station_id is not None:
        return station_id
    return wmo_to_ghcn_id(wmo_index, allow_downloads=allow_downloads)


def _canonical_missing_row_counts(df: pd.DataFrame) -> int:
    """Number of UTC hours in the calendar year (first 8760/8784 rows) lacking
    any observation. Used by the ``auto`` source policy to compare against
    ``max_missing_amy_rows`` for GHCNh data analogously to ISD-Lite."""
    if df.empty:
        return 0
    n_hours_year = len(df) - 23  # year + 23 tail hours of year+1
    year_slice = df.iloc[:n_hours_year]
    fully_missing = year_slice.isna().all(axis=1).sum()
    return int(fully_missing)


def _load_observations(
    *,
    wmo_index: int,
    year: int,
    source: str,
    station_id: Optional[str],
    amy_dir: Optional[str],
    amy_files: Optional[Tuple[str, str]],
    allow_downloads: bool,
    max_missing_amy_rows: Optional[int],
) -> Tuple[pd.DataFrame, str]:
    """Load AMY observations for ``year`` (and a 23-hour year+1 UTC tail).

    Returns the canonical SI-unit DataFrame and the source path that produced
    the year's data. The DataFrame index is naive UTC hourly timestamps from
    Jan 1 00:00 UTC of ``year`` through Jan 1 22:00 UTC of ``year + 1``.
    """
    if source not in _VALID_SOURCES:
        raise ValueError(f"source must be one of {_VALID_SOURCES}, got {source!r}")

    if source == "ghcnh":
        resolved = _resolve_station_id(wmo_index, station_id, allow_downloads)
        canonical, year_path = _load_ghcnh_year_canonical(
            station_id=resolved,
            year=year,
            amy_dir=amy_dir,
            amy_files=amy_files,
            allow_downloads=allow_downloads,
        )
        if max_missing_amy_rows is not None:
            missing = _canonical_missing_row_counts(canonical)
            if missing > max_missing_amy_rows:
                raise Exception(
                    f"GHCNh file {year_path} is missing {missing} hourly observations, "
                    f"but maximum allowed is {max_missing_amy_rows}"
                )
        return canonical, year_path

    if source == "isd_lite":
        canonical, year_path = _load_isd_lite_year_canonical(
            wmo_index=wmo_index,
            year=year,
            amy_dir=amy_dir,
            amy_files=amy_files,
            allow_downloads=allow_downloads,
            max_missing_amy_rows=max_missing_amy_rows,
        )
        return canonical, year_path

    # source == "auto": try ISD-Lite first, then GHCNh
    try:
        canonical, year_path = _load_isd_lite_year_canonical(
            wmo_index=wmo_index,
            year=year,
            amy_dir=amy_dir,
            amy_files=amy_files,
            allow_downloads=allow_downloads,
            max_missing_amy_rows=max_missing_amy_rows,
        )
        return canonical, year_path
    except _IsdLiteIncompleteError as exc:
        _logger.warning(
            "ISD-Lite for WMO %s year %s is too sparse (%s missing rows > %s); "
            "falling back to GHCNh.",
            wmo_index,
            year,
            exc.missing,
            exc.allowed,
        )
    except Exception as exc:
        _logger.warning(
            "ISD-Lite source failed for WMO %s year %s (%s); falling back to GHCNh.",
            wmo_index,
            year,
            exc,
        )

    resolved = _resolve_station_id(wmo_index, station_id, allow_downloads)
    canonical, year_path = _load_ghcnh_year_canonical(
        station_id=resolved,
        year=year,
        amy_dir=amy_dir,
        amy_files=None,  # in auto mode amy_files refers to the ISD-Lite pair only
        allow_downloads=allow_downloads,
    )
    if max_missing_amy_rows is not None:
        missing = _canonical_missing_row_counts(canonical)
        if missing > max_missing_amy_rows:
            raise Exception(
                f"GHCNh file {year_path} is missing {missing} hourly observations, "
                f"but maximum allowed is {max_missing_amy_rows}"
            )
    return canonical, year_path


def create_amy_epw_file(
    wmo_index: int,
    year: int,
    *,
    max_records_to_interpolate: int = 6,
    max_records_to_impute: int = 48,
    max_missing_amy_rows: int = 700,
    amy_epw_dir: str = None,
    tmy_epw_dir: str = None,
    amy_dir: str = None,
    amy_files: Tuple[str, str] = None,
    allow_downloads: bool = False,
    source: str = "auto",
    station_id: Optional[str] = None,
) -> str:
    """
    Combine data from a Typical Meteorological Year (TMY) EPW file and Actual Meteorological Year (AMY)
    observed data to generate an AMY EPW file for a single calendar year at a given WMO.

    :param wmo_index: The WMO Index of the weather station for which the EPW file should be generated.
        Currently only weather stations in the United States are supported.
    :param year: The year for which the EPW should be generated
    :param amy_epw_dir: The directory into which the generated AMY EPW file should be written.
        If not defined, a temporary directory will be created
    :param tmy_epw_dir: The source directory for TMY EPW files. If a file for the requested WMO Index is
        already present, it will be used. Otherwise a TMY EPW file will be downloaded.
    :param amy_dir: The source directory for AMY files. If a file for the requested station/year is
        already present, it will be used; otherwise the file is downloaded from NOAA (for ISD-Lite) or
        NCEI (for GHCNh). If not given, a package-default directory is used per source.
    :param amy_files: A 2-tuple of (year_file, next_year_file) absolute paths. The format must match
        ``source`` (whitespace-delimited ISD-Lite gz/csv or PSV GHCNh, respectively). When using ISD-Lite
        with ``amy_dir`` and ``allow_downloads=True``, a placeholder successor-year segment is synthesized
        if NOAA has not published it yet (see logs).
    :param max_records_to_interpolate: The maximum length of sequence for which linear interpolation will
        be used to replace missing values.
    :param max_records_to_impute: The maximum length of sequence for which imputation will be used to
        replace missing values.
    :param max_missing_amy_rows: The maximum total number of missing rows to permit in a year's AMY file.
    :param allow_downloads: If True, any missing TMY/AMY files required to generate the EPW will be
        downloaded from publicly available online catalogs. Otherwise, missing files raise an error.
    :param source: One of ``"auto"`` (default), ``"isd_lite"`` or ``"ghcnh"``.

        - ``"isd_lite"`` uses NOAA's legacy ISD-Lite product. NOAA discontinued updates to ISD-Lite in
          August 2025, so files for that year (and later) may be substantially incomplete.
        - ``"ghcnh"`` uses NOAA/NCEI's replacement Global Historical Climatology Network hourly (GHCNh)
          PSV files.
        - ``"auto"`` (default) tries ISD-Lite first and transparently retries with GHCNh if the
          ISD-Lite file is too incomplete to satisfy ``max_missing_amy_rows``.
    :param station_id: Optional GHCN station identifier (e.g. ``"USW00024233"``) used when the GHCNh
        source is engaged. If ``None``, the GHCN ID is looked up via the WMO -> GHCN mapping shipped
        with diyepw; pass an explicit value if your station is not in that mapping.
    :return: The absolute path of the generated AMY EPW file.
    """

    if amy_dir is not None and amy_files is not None:
        raise Exception("It is not possible to specify both amy_dir and amy_files")

    if source not in _VALID_SOURCES:
        raise ValueError(f"source must be one of {_VALID_SOURCES}, got {source!r}")

    if amy_epw_dir is None:
        global _tempdir_amy_epw
        amy_epw_dir = _tempdir_amy_epw
        _logger.info(
            f"No amy_epw_dir was specified - generated AMY EPWs will be stored in {amy_epw_dir}"
        )

    # Read in the corresponding TMY3 EPW file.
    tmy_epw_file_path = get_tmy_epw_file(wmo_index, tmy_epw_dir, allow_downloads=allow_downloads)
    tmy = Meteorology.from_tmy3_file(tmy_epw_file_path)

    # If the year we are generating an AMY EPW for is a leap year, then we need to add the leap day to the TMY data.
    # We'll do that by adding the day with all empty values, then using the same routine we do to interpolate/impute
    # missing data in our AMY files to fill in the missing data.
    if isleap(year):
        _logger.info(
            f"{year} is a leap year, using the interpolation strategy to populate TMY data for Feb. 29"
        )
        for hour in range(1, 25):
            col_names = tmy.observations.columns.to_list()
            new_row_vals = [1982, 2, 29, hour, 0]
            new_row_vals.extend(np.repeat(np.nan, len(col_names) - len(new_row_vals)))
            new_row = pd.DataFrame([new_row_vals], columns=col_names)
            tmy.observations = pd.concat([tmy.observations, new_row], ignore_index=True)

        # We sort by month, day and hour. We do *not* sort by year, because the year column doesn't matter and because
        # it is in any case not consistent throughout a TMY data set
        tmy.observations = tmy.observations.sort_values(by=["month", "day", "hour"])

        _handle_missing_values(
            tmy.observations,
            max_to_interpolate=0,  # We only want the imputation strategy to be used for the 24 missing hours
            max_to_impute=24,
            step=1,
            imputation_range=14 * 24,  # Two weeks, in hours
            imputation_step=24,
            ignore_columns=["Flags"],  # The TMY files we use seem to be missing data for this field entirely
        )

    amy_epw_file_name = (
        f"{tmy.country}_{tmy.state}_{tmy.city}.{tmy.station_number}_AMY_{year}.epw"
    )
    amy_epw_file_name = amy_epw_file_name.replace(" ", "-")
    amy_epw_file_path = os.path.join(amy_epw_dir, amy_epw_file_name)

    if os.path.exists(amy_epw_file_path):
        _logger.info(
            f"File already exists at {amy_epw_file_path}, so a new one won't be generated."
        )
        return amy_epw_file_path

    amy_df, _year_path = _load_observations(
        wmo_index=wmo_index,
        year=year,
        source=source,
        station_id=station_id,
        amy_dir=amy_dir,
        amy_files=amy_files,
        allow_downloads=allow_downloads,
        max_missing_amy_rows=max_missing_amy_rows,
    )

    # Shift the timestamp (index) to match the time zone of the WMO station.
    amy_df = amy_df.shift(periods=tmy.timezone_gmt_offset, freq="h")

    # Remove time steps that aren't applicable to the year of interest
    amy_df = _map_noaa_df_to_year(amy_df, year)

    _handle_missing_values(
        amy_df,
        step=pd.Timedelta("1h"),
        max_to_interpolate=max_records_to_interpolate,
        max_to_impute=max_records_to_impute,
        imputation_range=pd.Timedelta("2w"),
        imputation_step=pd.Timedelta("1d"),
        missing_values=[np.nan],
    )

    # Initialize new column for station pressure (not strictly necessary)
    amy_df["Station_Pressure"] = None

    # Convert sea level pressure (hPa) to atmospheric station pressure in Pa.
    for index in amy_df.index:
        stp = _convert_sea_level_pressure_to_station_pressure(
            amy_df["Sea_Level_Pressure"][index], tmy.elevation
        )
        amy_df.loc[index, "Station_Pressure"] = stp

    # Change observation values to the values taken from the AMY data
    tmy.set("year", year)
    tmy.set("Tdb", amy_df["Air_Temperature"].tolist())  # already °C
    tmy.set("Tdew", amy_df["Dew_Point_Temperature"].tolist())  # already °C
    tmy.set("Patm", amy_df["Station_Pressure"])
    tmy.set("Wdir", amy_df["Wind_Direction"])
    tmy.set("Wspeed", amy_df["Wind_Speed"].tolist())  # already m/s

    epw_rule_violations = tmy.validate_against_epw_rules()
    if len(epw_rule_violations) > 0:
        raise Exception("EPW validation failed:\n" + "\n".join(epw_rule_violations))

    tmy.write_epw(amy_epw_file_path)

    return amy_epw_file_path


def _map_noaa_df_to_year(df, year):
    """Reindex a UTC-shifted DataFrame to the full hourly grid for ``year``.

    The input is assumed to have a naive ``DatetimeIndex`` covering at least the
    target year. After ``df.shift(periods=tmy_offset, freq='h')`` the index is in
    local station time, so this trims/pads to that year's local hourly grid.
    """
    all_timestamps = pd.date_range(
        f"{year}-01-01 00:00:00", f"{year}-12-31 23:00:00", freq="h"
    )
    all_timestamps = pd.DataFrame(all_timestamps, columns=["timestamp"])

    df = pd.merge(all_timestamps, df, how="left", left_on="timestamp", right_index=True)
    df = df.set_index("timestamp")

    return df


def _handle_missing_values(
    df: pd.DataFrame,
    *,
    step,
    max_to_interpolate: int,
    max_to_impute: int,
    imputation_range,
    imputation_step,
    missing_values: list = None,
    ignore_columns=[],
):
    """
    Look for missing values in a DataFrame. If possible, the missing values will be
    populated in place, using one of two strategies:

    If the missing values are in a contiguous block up to the length defined by max_to_interpolate,
    the values will linearly interpolated using the previous and following values.

    Otherwise, if the missing values are in a contiguous block up to the length defined by
    max_to_impute, the values will be imputed by going back through the indices by
    imputation_range, then stepping through by step sizes defined by imputation_step
    until the index that is imputation_range ahead of the missing value is found, and
    averaging all values encountered.

    Otherwise, if the DataFrame contains at least one contiguous block of missing values
    larger than max_to_impute, an Exception will be raised.
    """

    if missing_values is None:  # pragma: no cover - We don't currently have any calls that don't specify this argument
        missing_values = [np.nan]

    def get_indices_to_replace(df, col_name):
        indices_to_replace = df.index[df[col_name].isna()].tolist()
        indices_to_replace = _split_list_into_contiguous_segments(
            indices_to_replace,
            step=step,
        )
        return indices_to_replace

    for col_name in (c for c in df if c not in ignore_columns):

        if df[col_name].isin(missing_values).any():
            df.loc[df[col_name].isin(missing_values), col_name] = np.nan

        indices_to_replace = get_indices_to_replace(df, col_name)

        if len(indices_to_replace) == 0:  # pragma: no cover
            continue

        max_sequence_length = len(max(indices_to_replace, key=len))

        if max_sequence_length > max_to_impute:  # pragma: no cover - We check for this case before this function is called
            raise Exception(
                "The longest set of missing records for {} is {}, but the max allowed is {}".format(
                    col_name, max_sequence_length, max_to_impute
                )
            )

        for indices in indices_to_replace:
            if len(indices) <= max_to_interpolate:
                continue

            indices_to_impute = indices[1:-1]

            for index_to_impute in indices_to_impute:
                replacement_value_index = index_to_impute - imputation_range
                replacement_values = []
                while replacement_value_index <= index_to_impute + imputation_range:
                    if replacement_value_index in df.index:
                        replacement_values.append(df[col_name][replacement_value_index])
                    replacement_value_index += imputation_step

                df.loc[index_to_impute, col_name] = pd.Series(
                    replacement_values, dtype=np.float64
                ).mean()

        df[col_name] = df[col_name].interpolate()


def _split_list_into_contiguous_segments(l: list, step):
    """Split a sorted, de-duplicated list into contiguous segments."""

    l = list(set(l))
    l.sort()

    segments = []
    cur_segment = []
    prev_val = None
    for val in l:
        if prev_val is not None and val - step != prev_val:
            segments.append(cur_segment)
            cur_segment = [val]
        else:
            cur_segment.append(val)
        prev_val = val
    if len(cur_segment) > 0:
        segments.append(cur_segment)

    return segments


def _convert_sea_level_pressure_to_station_pressure(slp_hpa, h_m) -> object:
    """Return the atmospheric station pressure in Pa given sea level pressure in hPa
    and station elevation in m.
    """

    slp_hpa = float(slp_hpa)
    h_m = float(h_m)

    Pa_inHg = slp_hpa * 0.029529983071445

    Pstn_inHg = Pa_inHg * ((288 - 0.0065 * h_m) / 288) ** 5.2561

    Pstn = Pstn_inHg * 3386.389

    return Pstn
