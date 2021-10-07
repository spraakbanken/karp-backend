# import pytest  # pyre-ignore
# import json
import time

from karp.tests.utils import get_json
from karp.utility.time import utc_now

# def init(fa_client_w_places_w_municipalities_scope_module, es_status_code):
#     if es_status_code == "skip":
#         pytest.skip("elasticsearch disabled")
#     return fa_client_w_places_w_municipalities_scope_module(use_elasticsearch=True)


def test_add(fa_client_w_places_w_municipalities_scope_module):

    before_add = utc_now()
    entry = {"code": 11, "name": "11", "municipality": [11]}

    fa_client_w_places_w_municipalities_scope_module.post(
        "places/add",
        json={"entry": entry},
        headers={"Authorization": "Bearer 1234"},
    )

    result = get_json(
        fa_client_w_places_w_municipalities_scope_module,
        "/entries/places/11",
        headers={"Authorization": "Bearer 1234"},
    )
    print(f"result = {result}")
    assert result["hits"][0]["version"] == 1
    assert result["hits"][0]["last_modified_by"] == "dummy"
    assert result["hits"][0]["last_modified"] > before_add


def test_no_changes_update(fa_client_w_places_w_municipalities_scope_module):

    entry = {"code": 12, "name": "12", "municipality": [1]}
    fa_client_w_places_w_municipalities_scope_module.post(
        "places/add", json={"entry": entry}, headers={"Authorization": "Bearer 1234"}
    )

    fa_client_w_places_w_municipalities_scope_module.post(
        "places/12/update",
        json={"entry": entry, "message": "message", "version": 1},
        headers={"Authorization": "Bearer 1234"},
    )

    result = get_json(
        fa_client_w_places_w_municipalities_scope_module,
        "/entries/places/12",
        headers={"Authorization": "Bearer 1234"},
    )
    print(f"result = {result}")
    assert result["hits"][0]["version"] == 1


def test_update(fa_client_w_places_w_municipalities_scope_module):

    entry = {"code": 13, "name": "13", "municipality": [13]}
    fa_client_w_places_w_municipalities_scope_module.post(
        "places/add", json={"entry": entry}, headers={"Authorization": "Bearer 1234"}
    )
    before_update = utc_now()

    entry["name"] = "13-2"
    response = fa_client_w_places_w_municipalities_scope_module.post(
        "places/13/update",
        json={"entry": entry, "message": "message", "version": 1},
        headers={"Authorization": "Bearer 1234"},
    )
    assert response.status_code == 200
    after_update = utc_now()

    result = get_json(
        fa_client_w_places_w_municipalities_scope_module,
        "/entries/places/13",
        headers={"Authorization": "Bearer 1234"},
    )
    assert result["hits"][0]["version"] == 2
    assert result["hits"][0]["last_modified"] > before_update
    assert result["hits"][0]["last_modified"] < after_update


# def test_conflict(fa_client_w_places_w_municipalities_scope_module):

#     entry = {"code": 1, "name": "1", "municipality": [1]}
#     fa_client_w_places_w_municipalities_scope_module.post(
#         "places/add", json={"entry": entry}, headers={"Authorization": "Bearer 1234"}
#     )

#     entry["name"] = "2"
#     fa_client_w_places_w_municipalities_scope_module.post(
#         "places/1/update",
#         json={"entry": entry, "message": "message", "version": 1},
#         headers={"Authorization": "Bearer 1234"},
#     )

#     entry["name"] = "1"

#     response = fa_client_w_places_w_municipalities_scope_module.post(
#         "places/1/update",
#         json={"entry": entry, "message": "message", "version": 1},
#         headers={"Authorization": "Bearer 1234"},
#     )

#     assert response.status_code == 400
#     error_obj = json.loads(response.data.decode())
#     assert "Version" in error_obj["error"]
#     assert "diff" in error_obj


# def test_delete(fa_client_w_places_w_municipalities_scope_module):
#     fa_client_w_places_w_municipalities_scope_module = init(fa_client_w_places_w_municipalities_scope_module, es)

#     entry = {"code": 1, "name": "1", "municipality": [1]}
#     fa_client_w_places_w_municipalities_scope_module.post(
#         "places/add", json={"entry": entry}), headers={"Authorization": "Bearer 1234"}
#     )

#     fa_client_w_places_w_municipalities_scope_module.delete("places/1/delete")

#     # TODO query history about changes, when we have a history api


# def test_reindex(fa_client_w_places_w_municipalities_scope_module):
#     fa_client_w_places_w_municipalities_scope_module = init(fa_client_w_places_w_municipalities_scope_module, es)

#     entry = {"code": 1, "name": "1", "municipality": [1]}
#     fa_client_w_places_w_municipalities_scope_module.post(
#         "places/add", json={"entry": entry}), headers={"Authorization": "Bearer 1234"}
#     )

#     for i in range(2, 10):
#         entry["name"] = str(i)
#         fa_client_w_places_w_municipalities_scope_module.post(
#             "places/1/update",
#             json={"entry": entry, "message": "message", "version": i}),
#             headers={"Authorization": "Bearer 1234"},
#         )

#     with fa_client_w_places_w_municipalities_scope_module.application.app_context():
#         import karp.indexmgr as indexmgr

#         indexmgr.publish_index("places")

#     result = get_json(fa_client_w_places_w_municipalities_scope_module, "places/query")
#     assert result["hits"][0]["version"] == 9
#     assert len(result["hits"]) == 1


# def test_force_update(fa_client_w_places_w_municipalities_scope_module):
#     fa_client_w_places_w_municipalities_scope_module = init(fa_client_w_places_w_municipalities_scope_module, es)

#     entry = {"code": 1, "name": "1", "municipality": [1]}
#     fa_client_w_places_w_municipalities_scope_module.post(
#         "places/add", json={"entry": entry}), headers={"Authorization": "Bearer 1234"}
#     )

#     entry["name"] = "2"
#     fa_client_w_places_w_municipalities_scope_module.post(
#         "places/1/update",
#         json={"entry": entry, "message": "message", "version": 1}),
#         headers={"Authorization": "Bearer 1234"},
#     )

#     entry["name"] = "1"

#     response = fa_client_w_places_w_municipalities_scope_module.post(
#         "places/1/update",
#         json={"entry": entry, "message": "message", "version": 1}),
#         headers={"Authorization": "Bearer 1234"},
#     )

#     assert response.status_code == 400
#     error_obj = json.loads(response.data.decode())
#     assert "Version" in error_obj["error"]
#     assert error_obj["errorCode"] == 33

#     response = fa_client_w_places_w_municipalities_scope_module.post(
#         "places/1/update?force=true",
#         json={"entry": entry, "message": "message", "version": 1}),
#         headers={"Authorization": "Bearer 1234"},
#     )

#     assert response.status_code == 200

#     result = get_json(fa_client_w_places_w_municipalities_scope_module, "places/1")
#     assert result["hits"][0]["entry"]["name"] == "1"
