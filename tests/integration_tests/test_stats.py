import time

import pytest

from tests.utils import get_json


@pytest.mark.skip(reason="dependent of order of tests")
def test_stats(client_with_entries_scope_session):
    time.sleep(5)
    entries = get_json(client_with_entries_scope_session, "/query/places")
    assert len(entries) == 9

    entries = get_json(client_with_entries_scope_session, "/stats/places/area")
    assert len(entries) == 4
