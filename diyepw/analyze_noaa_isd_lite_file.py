"""Backward-compatible shim for the generalized AMY file analyzer.

The original ``analyze_noaa_isd_lite_file`` function only handled NOAA
ISD-Lite files. With the addition of GHCNh support, the generalized
implementation lives in :mod:`diyepw.analyze_amy_file`.
"""

from .analyze_amy_file import analyze_amy_file


def analyze_noaa_isd_lite_file(file: str, compression: str = "infer"):
    """Analyze a single NOAA ISD-Lite file (kept for backward compatibility).

    See :func:`diyepw.analyze_amy_file.analyze_amy_file` for the generalized
    interface that also supports GHCN-hourly PSV files.
    """
    return analyze_amy_file(file, format="isd_lite", compression=compression)
