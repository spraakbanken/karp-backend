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
        result = _next_up(result)
    _previous = result
    return result


def _next_up(x: float) -> float:
    if math.isnan(x) or (math.isinf(x) and x > 0):
        return x

    if x == 0.0:
        x = 0.0

    n = struct.unpack("<q", struct.pack("<d", x))[0]
    if n >= 0:
        n += 1
    else:
        n -= 1
    return struct.unpack("<d", struct.pack("<q", n))[0]
