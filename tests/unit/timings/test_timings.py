from karp.timings import monotonic_utc_now, utc_now


def test_monotonic_utc_now_is_monotonic() -> None:
    assert monotonic_utc_now() < monotonic_utc_now()


def test_utc_now_is_monotonic_maybe() -> None:
    assert utc_now() <= utc_now()
