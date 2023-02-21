from karp.timings import monotonic_utc_now, utc_now


def test_monotonic_utc_now_is_monotonic():
    assert monotonic_utc_now() < monotonic_utc_now()
