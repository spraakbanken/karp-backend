from karp.foundation.timings import utc_now
from tests.utils import get_json


def test_id(fa_data_client):
    entries = get_json(fa_data_client, "/query/places")
    test_entry = entries["hits"][3]
    _id = test_entry["id"]
    name = test_entry["entry"]["name"]

    entries = get_json(fa_data_client, f'/query/places?q=equals|@id|"{_id}"')
    assert len(entries["hits"]) == 1
    assert entries["hits"][0]["entry"]["name"] == name

    # check if it works without quotes
    entries = get_json(fa_data_client, f"/query/places?q=equals|@id|{_id}")
    assert len(entries["hits"]) == 1
    assert entries["hits"][0]["entry"]["name"] == name


def test_last_modified(fa_data_client):
    now = utc_now()
    for op in ["lte", "lt", "gte", "gt"]:
        entries = get_json(fa_data_client, f"/query/places?q={op}|@last_modified|{now:.3f}&size=100")
        if op[0] == "l":
            # lt and lte should return all hits
            assert len(entries["hits"]) == 23
        else:
            # gt and gte should return 0 hits
            assert len(entries["hits"]) == 0


def test_last_modified_by_not_existing_user(fa_data_client):
    entries = get_json(fa_data_client, f"/query/places?q=equals|@last_modified_by|asdjhadsjfh132252")
    assert len(entries["hits"]) == 0
    assert entries["total"] == 0


def test_last_modified_by_existing_user(fa_data_client):
    entries = get_json(fa_data_client, f"/query/places?q=equals|@last_modified_by|abc123&size=100")
    assert len(entries["hits"]) == 20
    assert entries["total"] == 20
