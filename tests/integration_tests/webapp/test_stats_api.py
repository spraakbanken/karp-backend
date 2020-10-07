from tests.utils import get_json


def test_stats(client_with_entries_scope_session):
    entries = get_json(client_with_entries_scope_session, "places/stats/area")

    assert len(entries) == 4
