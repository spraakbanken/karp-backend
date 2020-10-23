import json
import pytest  # pyre-ignore
import time
from datetime import datetime, timezone

import karp.resourcemgr.entryread as entryread
from karp.errors import ClientErrorCodes
from tests.utils import get_json


def init(client, es_status_code, entries):
    if es_status_code == "skip":
        pytest.skip("elasticsearch disabled")
    client_with_data = client(use_elasticsearch=True)

    for entry in entries:
        client_with_data.post(
            "places/add",
            data=json.dumps({"entry": entry}),
            content_type="application/json",
        )
    return client_with_data


def test_add(es, client_with_data_f):
    client = init(client_with_data_f, es, [])

    response = client.post(
        "places/add",
        data=json.dumps(
            {
                "entry": {
                    "code": 3,
                    "name": "test3",
                    "population": 4,
                    "area": 50000,
                    "density": 5,
                    "municipality": [2, 3],
                }
            }
        ),
        content_type="application/json",
    )
    response_data = json.loads(response.data.decode())
    assert "newID" in response_data
    assert "3" == response_data["newID"]

    entries = get_json(client, "/query/places")
    assert len(entries["hits"]) == 1
    assert entries["hits"][0]["entry"]["name"] == "test3"


def test_add_existing(es, client_with_data_f):
    client = init(client_with_data_f, es, [])

    response = client.post(
        "places/add",
        data=json.dumps(
            {
                "entry": {
                    "code": 3,
                    "name": "test3",
                    "population": 4,
                    "area": 50000,
                    "density": 5,
                    "municipality": [2, 3],
                }
            }
        ),
        content_type="application/json",
    )
    assert 200 <= response.status_code < 300

    response = client.post(
        "places/add",
        data=json.dumps(
            {
                "entry": {
                    "code": 3,
                    "name": "test3",
                    "population": 4,
                    "area": 50000,
                    "density": 5,
                    "municipality": [2, 3],
                }
            }
        ),
        content_type="application/json",
    )
    assert response.status_code == 400
    response_data = json.loads(response.data.decode())

    assert "error" in response_data
    assert "errorCode" in response_data
    assert ClientErrorCodes.DB_INTEGRITY_ERROR == response_data["errorCode"]
    assert "Database error" in response_data["error"]


def test_delete(es, client_with_data_f):
    client = init(
        client_with_data_f,
        es,
        [
            {
                "code": 3,
                "name": "test3",
                "population": 4,
                "area": 50000,
                "density": 5,
                "municipality": [2, 3],
            }
        ],
    )

    entries = get_json(client, "/query/places")
    entry_id = entries["hits"][0]["id"]

    client.delete("places/%s/delete" % entry_id)

    entries = get_json(client, "/query/places")
    assert len(entries["hits"]) == 0


def test_update(es, client_with_data_f):
    client = init(
        client_with_data_f,
        es,
        [
            {
                "code": 3,
                "name": "test3",
                "population": 4,
                "area": 50000,
                "density": 5,
                "municipality": [2, 3],
            }
        ],
    )

    entries = get_json(client, "/query/places")
    entry_id = entries["hits"][0]["id"]

    response = client.post(
        "places/%s/update" % entry_id,
        data=json.dumps(
            {
                "entry": {
                    "code": 3,
                    "name": "test3",
                    "population": 5,
                    "area": 50000,
                    "density": 5,
                    "municipality": [2, 3],
                },
                "message": "changes",
                "version": 1,
            }
        ),
        content_type="application/json",
    )
    response_data = json.loads(response.data.decode())
    assert "newID" in response_data
    assert "3" == response_data["newID"]

    entries = get_json(client, "/query/places")
    assert len(entries["hits"]) == 1
    assert entries["hits"][0]["id"] == entry_id
    assert entries["hits"][0]["entry"]["population"] == 5


def test_update_entry_id(es, client_with_data_f):
    client = init(
        client_with_data_f,
        es,
        [
            {
                "code": 3,
                "name": "test3",
                "population": 4,
                "area": 50000,
                "density": 5,
                "municipality": [2, 3],
            }
        ],
    )

    entries = get_json(client, "/query/places")
    entry_id = entries["hits"][0]["id"]

    response = client.post(
        "places/%s/update" % entry_id,
        data=json.dumps(
            {
                "entry": {
                    "code": 4,
                    "name": "test3",
                    "population": 5,
                    "area": 50000,
                    "density": 5,
                    "municipality": [2, 3],
                },
                "message": "changes",
                "version": 1,
            }
        ),
        content_type="application/json",
    )
    response_data = json.loads(response.data.decode())
    assert "newID" in response_data
    assert "4" == response_data["newID"]

    # check that the old entry with old id has been removed
    entries = get_json(client, "/query/places")
    assert 1 == len(entries["hits"])


def test_update_via_get_doesnt_mess_up(es, client_with_data_f):
    client = init(
        client_with_data_f,
        es,
        [
            {
                "code": 1,
                "name": "test1",
                "population": 10,
                "area": 50000,
                "density": 5,
                "municipality": [2, 3],
            },
            {
                "code": 2,
                "name": "test2",
                "population": 5,
                "larger_place": 1,
                "area": 50000,
                "density": 5,
                "municipality": [2, 3],
            },
        ],
    )

    entries = get_json(client, "/query/places")
    assert len(entries["hits"]) == 2
    entry_id = entries["hits"][0]["id"]
    assert entry_id == "1"

    response = client.get(
        "places/%s/update" % entry_id,
        data=json.dumps(
            {
                "entry": {
                    "code": 4,
                    "name": "test3",
                    "population": 5,
                    "area": 50000,
                    "density": 5,
                    "municipality": [2, 3],
                },
                "message": "changes",
                "version": 1,
            }
        ),
        content_type="application/json",
    )
    assert response.status_code == 400
    # response_data = json.loads(response.data.decode())
    # assert "newID" in response_data
    # assert "4" == response_data["newID"]

    # check that the old entry with old id has been removed
    entries = get_json(client, "/query/places")
    assert 2 == len(entries["hits"])
    # for val in entries["hits"]:
    #     assert "entry" in val
    #     entry = val["entry"]
    #     print("entry = {}".format(entry))
    #     if entry["code"] == 1:
    #         assert "v_larger_place" not in entry
    #         assert "larger_place" not in entry
    #         assert "v_smaller_places" in entry
    #         assert entry["v_smaller_places"][0]["code"] == 2
    #     else:
    #         assert entry["v_larger_place"]["code"] == 1
    #         assert entry["v_larger_place"]["name"] == "test1"
    #         assert "v_smaller_places" not in entry


def test_refs(es, client_with_data_f):
    client = init(
        client_with_data_f,
        es,
        [
            {
                "code": 1,
                "name": "test1",
                "population": 10,
                "area": 50000,
                "density": 5,
                "municipality": [2, 3],
            },
            {
                "code": 2,
                "name": "test2",
                "population": 5,
                "larger_place": 1,
                "area": 50000,
                "density": 5,
                "municipality": [2, 3],
            },
        ],
    )

    entries = get_json(client, "/query/places")
    assert len(entries["hits"]) == 2
    for val in entries["hits"]:
        assert "entry" in val
        entry = val["entry"]
        print("entry = {}".format(entry))
        if entry["code"] == 1:
            assert "v_larger_place" not in entry
            assert "larger_place" not in entry
            assert "v_smaller_places" in entry
            assert entry["v_smaller_places"][0]["code"] == 2
        else:
            assert entry["v_larger_place"]["code"] == 1
            assert entry["v_larger_place"]["name"] == "test1"
            assert "v_smaller_places" not in entry


def test_external_refs(es, client_with_data_f):
    client = init(
        client_with_data_f,
        es,
        [
            {
                "code": 1,
                "name": "test1",
                "population": 10,
                "area": 50000,
                "density": 5,
                "municipality": [1],
            },
            {
                "code": 2,
                "name": "test2",
                "population": 5,
                "larger_place": 1,
                "area": 50000,
                "density": 5,
                "municipality": [1, 2],
            },
            {
                "code": 3,
                "name": "test2",
                "population": 5,
                "larger_place": 1,
                "area": 50000,
                "density": 5,
                "municipality": [2],
            },
        ],
    )

    client.post(
        "municipalities/add",
        data=json.dumps(
            {
                "entry": {
                    "code": 1,
                    "name": "municipality1",
                    "state": "state1",
                    "region": "region1",
                }
            }
        ),
        content_type="application/json",
    )

    client.post(
        "municipalities/add",
        data=json.dumps(
            {
                "entry": {
                    "code": 2,
                    "name": "municipality2",
                    "state": "state2",
                    "region": "region2",
                }
            }
        ),
        content_type="application/json",
    )

    entries = get_json(client, "/query/municipalities")
    for val in entries["hits"]:
        assert "entry" in val
        entry = val["entry"]

        assert "v_places" in entry
        place_codes = [place["code"] for place in entry["v_places"]]
        assert len(place_codes) == 2
        if entry["code"] == 1:
            assert 1 in place_codes
            assert 2 in place_codes
        else:
            assert 2 in place_codes
            assert 3 in place_codes

    places_entries = get_json(client, "/query/places")
    for val in places_entries["hits"]:
        assert "entry" in val
        entry = val["entry"]
        assert "municipality" in entry
        assert isinstance(entry["v_municipality"], list)
        if entry["code"] == 2:
            assert {"code": 1, "name": "municipality1", "state": "state1"} in entry[
                "v_municipality"
            ]
            assert {"code": 2, "name": "municipality2", "state": "state2"} in entry[
                "v_municipality"
            ]


def test_update_refs(es, client_with_data_f):
    client = init(
        client_with_data_f,
        es,
        [
            {
                "code": 5,
                "name": "test1",
                "population": 10,
                "area": 50000,
                "density": 5,
                "municipality": [2, 3],
            },
            {
                "code": 6,
                "name": "test2",
                "population": 5,
                "larger_place": 5,
                "area": 50000,
                "density": 5,
                "municipality": [2, 3],
            },
        ],
    )

    entries = get_json(client, "/query/places")
    assert len(entries["hits"]) == 2
    for val in entries["hits"]:
        assert "entry" in val
        entry = val["entry"]
        print("entry = {}".format(entry))
        if entry["code"] == 5:
            assert "v_smaller_places" in entry
            assert entry["v_smaller_places"][0]["code"] == 6

    client.delete("/places/6/delete")

    entries = get_json(client, "/query/places")
    assert len(entries["hits"]) == 1
    entry = entries["hits"][0]
    assert "v_smaller_places" not in entry


def test_update_refs2(es, client_with_data_f):
    client = init(
        client_with_data_f, es, [{"code": 3, "name": "test3", "municipality": [2, 3]}]
    )

    client.post(
        "places/3/update",
        data=json.dumps(
            {
                "entry": {"code": 3, "name": "test3", "municipality": [2]},
                "message": "changes",
                "version": 1,
            }
        ),
        content_type="application/json",
    )

    entries = get_json(client, "/query/places")
    assert len(entries["hits"]) == 1
    assert entries["hits"][0]["id"] == "3"
    assert entries["hits"][0]["entry"]["municipality"] == [2]
    assert (
        "v_municipality" not in entries["hits"][0]
        or len(entries["hits"][0]["municipality"]) == 0
    )
    with client.application.app_context():
        db_entry = entryread.get_entry("places", "3")
        assert len(db_entry.municipality) == 1
        assert db_entry.municipality[0].municipality == 2


def test_last_modified(es, client_with_data_f):
    before_add = datetime.now(timezone.utc).timestamp()

    time.sleep(1)
    client = init(
        client_with_data_f, es, [{"code": 1, "name": "test1", "municipality": [1]}]
    )
    time.sleep(1)

    after_add = datetime.now(timezone.utc).timestamp()

    entries = get_json(client, "/query/places")
    hit = entries["hits"][0]
    assert "dummy" == hit["last_modified_by"]
    assert before_add < hit["last_modified"]
    assert after_add > hit["last_modified"]

    time.sleep(1)
    client.post(
        "places/1/update",
        data=json.dumps(
            {
                "entry": {"code": 1, "name": "test2", "municipality": [1]},
                "message": "changes",
                "version": 1,
            }
        ),
        content_type="application/json",
    )
    time.sleep(1)

    after_update = datetime.now(timezone.utc).timestamp()

    entries = get_json(client, "/query/places")
    hit = entries["hits"][0]
    assert "dummy" == hit["last_modified_by"]
    assert after_add < hit["last_modified"]
    assert after_update > hit["last_modified"]
