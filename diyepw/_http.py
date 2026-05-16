"""HTTP helpers shared across NOAA/NCEI data downloaders.

A central timeout is enforced because NOAA/NCEI hosts can stall for very long
durations, causing the AMY pipeline to appear hung. Bounded timeouts let
fallback paths (e.g. GHCNh) take over quickly when an upstream endpoint is
slow or unavailable.
"""

import urllib.request as request

DEFAULT_HTTP_TIMEOUT_SECONDS = 120


def urlopen(url: str, *, timeout: float = DEFAULT_HTTP_TIMEOUT_SECONDS):
    """Open *url* with a bounded timeout. Returns the raw urllib response object."""
    return request.urlopen(url, timeout=timeout)
