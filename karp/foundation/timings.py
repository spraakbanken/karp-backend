"""Time utilities."""

import math
import struct
from datetime import datetime, timezone


def utc_now() -> float:
    """A UTC timestamp in seconds.

    This function may return the same timestamp twice.
    """
    return datetime.now(timezone.utc).timestamp()


_previous: float = utc_now()


def monotonic_utc_now() -> float:
    """A UTC timestamp in seconds.

    This function will never return the same result twice.
    """
    global _previous
    result = utc_now()
    if result <= _previous:
        result = math.nextafter(result, math.inf)
    _previous = result
    return result
