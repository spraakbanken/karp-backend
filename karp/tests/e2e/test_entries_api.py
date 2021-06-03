# import json
# import time
# from datetime import datetime, timezone
# from unittest import mock

import pytest  # pyre-ignore

# from karp.application import ctx, config
# from karp.infrastructure.unit_of_work import unit_of_work


# import karp.resourcemgr.entryread as entryread
from karp.errors import ClientErrorCodes

# from tests.utils import get_json

# from tests.integration_tests.common_fixtures import (
#     fixture_fa_client_w_places,
#     fixture_places,
# )


# def init(client, es_status_code, entries):
#     if es_status_code == "skip":
#         pytest.skip("elasticsearch disabled")
#     client_with_data = client(use_elasticsearch=True)

#     for entry in entries:
#         client_with_data.post(
#             "places/add",
#             data=json.dumps({"entry": entry}),
#             content_type="application/json",
#         )
#     return client_with_data
pytestmark = pytest.mark.usefixtures("use_dummy_authenticator")  # , "use_main_index")


@pytest.mark.usefixtures("places_published")
@pytest.mark.usefixtures("main_db")
def test_add(fa_client):  # fa_client_w_places):
    # client = init(client_with_data_f, es, [])

    response = fa_client.post(
        "places/add",
        json={
            "entry": {
                "code": 3,
                "name": "test3",
                "population": 4,
                "area": 50000,
                "density": 5,
                "municipality": [2, 3],
            }
        },
        headers={"Authorization": "Bearer FAKETOKEN"},
    )
    print(f"response. = {response.json()}")
    assert response.status_code == 201
    response_data = response.json()
    assert "newID" in response_data
    assert response_data["newID"] == "3"

    from karp.webapp import app_config

    with app_config.bus.ctx.resource_uow as uw:
        resource = uw.repo.get_active_resource("places")

    with app_config.bus.ctx.entry_uows.get("places") as uw:
        entries = uw.repo.entry_ids()
        assert len(entries) == 1
        assert entries[0] == "3"
    # entries = get_json(client, "places/query")
    # assert len(entries["hits"]) == 1
    # assert entries["hits"][0]["entry"]["name"] == "test3"


# def test_add_existing(fa_client_w_places):
#     #     client = init(client_with_data_f, es, [])

#     response = fa_client_w_places.post(
#         "places/add",
#         json={
#             "entry": {
#                 "code": 3,
#                 "name": "test3",
#                 "population": 4,
#                 "area": 50000,
#                 "density": 5,
#                 "municipality": [2, 3],
#             }
#         },
#         headers={"Authorization": "Bearer 1234"},
#     )
#     print(f"response = {response.json()}")

#     assert response.status_code == 201

#     response = fa_client_w_places.post(
#         "places/add",
#         json={
#             "entry": {
#                 "code": 3,
#                 "name": "test3",
#                 "population": 4,
#                 "area": 50000,
#                 "density": 5,
#                 "municipality": [2, 3],
#             }
#         },
#         headers={"Authorization": "Bearer 1234"},
#     )
#     assert response.status_code == 400
#     response_data = response.json()

#     assert "error" in response_data
#     assert "errorCode" in response_data
#     assert ClientErrorCodes.DB_INTEGRITY_ERROR == response_data["errorCode"]
#     if config.DB_DRIVER == "sqlite":
#         pass
#     else:
#         assert response_data["error"] == "The key 'entry_id' is not unique (value='3')."


# def test_delete(fa_client_w_places):
#     response = fa_client_w_places.post(
#         "places/add",
#         json={
#             "entry": {
#                 "code": 3,
#                 "name": "test3",
#                 "population": 4,
#                 "area": 50000,
#                 "density": 5,
#                 "municipality": [2, 3],
#             }
#         },
#         headers={"Authorization": "Bearer 1234"},
#     )
#     print(f"response = {response.json()}")

#     assert response.status_code == 201

#     with unit_of_work(using=ctx.resource_repo) as uw:
#         resource = uw.get_active_resource("places")

#     with unit_of_work(using=resource.entry_repository) as uw:
#         entries = uw.entry_ids()
#         assert len(entries) == 1
#         assert entries[0] == "3"

#     entry_id = response.json()["newID"]

#     response = fa_client_w_places.delete(
#         f"places/{entry_id}/delete", headers={"Authorization": "Bearer 1234"}
#     )

#     assert response.status_code == 200

#     with unit_of_work(using=resource.entry_repository) as uw:
#         assert len(uw.entry_ids()) == 0


# def test_delete_non_existing_fails(fa_client_w_places):

#     entry_id = "non_existing_id"

#     response = fa_client_w_places.delete(
#         f"places/{entry_id}/delete", headers={"Authorization": "Bearer 1234"}
#     )

#     assert response.status_code == 400

#     response_data = response.json()

#     assert response_data["errorCode"] == ClientErrorCodes.ENTRY_NOT_FOUND

#     assert (
#         response_data["error"]
#         == f"Entry '{entry_id}' (version latest) not found. resource_id: places, version: latest"
#     )


# def test_update_non_existing_fails(fa_client_w_places):
#     entry_id = "3"
#     response = fa_client_w_places.post(
#         f"places/{entry_id}/update",
#         json={
#             "entry": {
#                 "code": 3,
#                 "name": "test3",
#                 "population": 5,
#                 "area": 50000,
#                 "density": 5,
#                 "municipality": [2, 3],
#             },
#             "message": "changes",
#             "version": 1,
#         },
#         headers={"Authorization": "Bearer 1234"},
#         #         ),
#         #         content_type="application/json",
#     )
#     assert response.status_code == 400
#     response_data = response.json()
#     assert response_data["errorCode"] == ClientErrorCodes.ENTRY_NOT_FOUND

#     assert (
#         response_data["error"]
#         == f"Entry '{entry_id}' (version 1) not found. resource_id: places, version: latest"
#     )


# def test_update_wo_changes_fails(fa_client_w_places):
#     response = fa_client_w_places.post(
#         "places/add",
#         json={
#             "entry": {
#                 "code": 3,
#                 "name": "test3",
#                 "population": 4,
#                 "area": 50000,
#                 "density": 5,
#                 "municipality": [2, 3],
#             }
#         },
#         headers={"Authorization": "Bearer 1234"},
#     )
#     print(f"response = {response.json()}")

#     assert response.status_code == 201
#     entry_id = response.json()["newID"]

#     with unit_of_work(using=ctx.resource_repo) as uw:
#         resource = uw.get_active_resource("places")

#     with unit_of_work(using=resource.entry_repository) as uw:
#         entries = uw.entry_ids()
#         assert len(entries) == 1
#         assert entries[0] == "3"
#         entry = uw.by_entry_id(entry_id)
#         assert entry.entry_id == entry_id
#         assert entry.body["population"] == 4

#     response = fa_client_w_places.post(
#         f"places/{entry_id}/update",
#         json={
#             "entry": {
#                 "code": 3,
#                 "name": "test3",
#                 "population": 4,
#                 "area": 50000,
#                 "density": 5,
#                 "municipality": [2, 3],
#             },
#             "message": "changes",
#             "version": 1,
#         },
#         headers={"Authorization": "Bearer 1234"},
#         #         ),
#         #         content_type="application/json",
#     )
#     assert response.status_code == 400
#     response_data = response.json()
#     assert response_data["errorCode"] == ClientErrorCodes.ENTRY_NOT_CHANGED

#     assert response_data["error"] == "No changes made"


# @pytest.mark.skip()
# def test_update_wrong_id(fa_client_w_places):
#     response = fa_client_w_places.post(
#         "places/add",
#         json={
#             "entry": {
#                 "code": 3,
#                 "name": "test3",
#                 "population": 4,
#                 "area": 50000,
#                 "density": 5,
#                 "municipality": [2, 3],
#             }
#         },
#         headers={"Authorization": "Bearer 1234"},
#     )
#     print(f"response = {response.json()}")

#     assert response.status_code == 201
#     entry_id = response.json()["newID"]

#     with unit_of_work(using=ctx.resource_repo) as uw:
#         resource = uw.get_active_resource("places")

#     with unit_of_work(using=resource.entry_repository) as uw:
#         entries = uw.entry_ids()
#         assert len(entries) == 1
#         assert entries[0] == "3"

#     response = fa_client_w_places.post(
#         f"places/{entry_id}/update",
#         json={
#             "entry": {
#                 "code": 4,
#                 "name": "test3",
#                 "population": 4,
#                 "area": 50000,
#                 "density": 5,
#                 "municipality": [2, 3],
#             },
#             "message": "changes",
#             "version": 1,
#         },
#         headers={"Authorization": "Bearer 1234"},
#         #         ),
#         #         content_type="application/json",
#     )
#     assert response.status_code == 400
#     response_data = response.json()
#     assert response_data["errorCode"] == ClientErrorCodes.ENTRY_ID_MISMATCH

#     assert response_data["error"] == "entry_id '4' does not equal '3'"


# def test_update_wrong_version_fails(fa_client_w_places):
#     response = fa_client_w_places.post(
#         "places/add",
#         json={
#             "entry": {
#                 "code": 3,
#                 "name": "test3",
#                 "population": 4,
#                 "area": 50000,
#                 "density": 5,
#                 "municipality": [2, 3],
#             }
#         },
#         headers={"Authorization": "Bearer 1234"},
#     )
#     print(f"response = {response.json()}")

#     assert response.status_code == 201
#     entry_id = response.json()["newID"]

#     with unit_of_work(using=ctx.resource_repo) as uw:
#         resource = uw.get_active_resource("places")

#     with unit_of_work(using=resource.entry_repository) as uw:
#         entries = uw.entry_ids()
#         assert len(entries) == 1
#         assert entries[0] == "3"
#         entry = uw.by_entry_id(entry_id)
#         assert entry.entry_id == entry_id
#         assert entry.body["population"] == 4

#     response = fa_client_w_places.post(
#         f"places/{entry_id}/update",
#         json={
#             "entry": {
#                 "code": 3,
#                 "name": "test3",
#                 "population": 5,
#                 "area": 50000,
#                 "density": 5,
#                 "municipality": [2, 3],
#             },
#             "message": "changes",
#             "version": 2,
#         },
#         headers={"Authorization": "Bearer 1234"},
#         #         ),
#         #         content_type="application/json",
#     )
#     assert response.status_code == 400
#     response_data = response.json()
#     assert response_data["errorCode"] == ClientErrorCodes.VERSION_CONFLICT

#     assert response_data["error"] == "Version conflict. Please update entry."
#     assert response_data["diff"] == [
#         {"type": "CHANGE", "field": "population", "before": 4, "after": 5}
#     ]


# def test_update(fa_client_w_places):
#     response = fa_client_w_places.post(
#         "places/add",
#         json={
#             "entry": {
#                 "code": 3,
#                 "name": "test3",
#                 "population": 4,
#                 "area": 50000,
#                 "density": 5,
#                 "municipality": [2, 3],
#             }
#         },
#         headers={"Authorization": "Bearer 1234"},
#     )
#     print(f"response = {response.json()}")

#     assert response.status_code == 201
#     entry_id = response.json()["newID"]

#     with unit_of_work(using=ctx.resource_repo) as uw:
#         resource = uw.get_active_resource("places")

#     with unit_of_work(using=resource.entry_repository) as uw:
#         entries = uw.entry_ids()
#         assert len(entries) == 1
#         assert entries[0] == "3"
#         entry = uw.by_entry_id(entry_id)
#         assert entry.entry_id == entry_id
#         assert entry.body["population"] == 4

#     response = fa_client_w_places.post(
#         f"places/{entry_id}/update",
#         json={
#             "entry": {
#                 "code": 3,
#                 "name": "test3",
#                 "population": 5,
#                 "area": 50000,
#                 "density": 5,
#                 "municipality": [2, 3],
#             },
#             "message": "changes",
#             "version": 1,
#         },
#         headers={"Authorization": "Bearer 1234"},
#         #         ),
#         #         content_type="application/json",
#     )
#     assert response.status_code == 200
#     response_data = response.json()
#     assert response_data["newID"] == "3"

#     #     entries = get_json(client, "places/query")
#     #     assert len(entries["hits"]) == 1
#     #     assert entries["hits"][0]["id"] == entry_id
#     #     assert entries["hits"][0]["entry"]["population"] == 5

#     with unit_of_work(using=resource.entry_repository) as uw:
#         assert len(uw.entry_ids()) == 1
#         entry = uw.by_entry_id(entry_id)
#         assert entry.entry_id == entry_id
#         assert entry.body["population"] == 5


# def test_update_several_times(fa_client_w_places):
#     response = fa_client_w_places.post(
#         "places/add",
#         json={"entry": {"code": 3, "name": "a", "municipality": [1]}},
#         headers={"Authorization": "Bearer 1234"},
#     )
#     assert response.status_code == 201
#     new_id = response.json()["newID"]
#     for i in range(2, 10):
#         response = fa_client_w_places.post(
#             f"places/{new_id}/update",
#             json={
#                 "entry": {"code": 3, "name": "a" * i, "municipality": [1]},
#                 "message": "changes",
#                 "version": i - 1,
#             },
#             headers={"Authorization": "Bearer 1234"},
#         )
#         print(f"i = {i}: response = {response.json()}")
#         assert response.status_code == 200


# def test_update_entry_id(fa_client_w_places):
#     response = fa_client_w_places.post(
#         "places/add",
#         json={
#             "entry": {
#                 "code": 3,
#                 "name": "test3",
#                 "population": 4,
#                 "area": 50000,
#                 "density": 5,
#                 "municipality": [2, 3],
#             }
#         },
#         headers={"Authorization": "Bearer 1234"},
#     )
#     assert response.status_code == 201
#     entry_id = response.json()["newID"]

#     response = fa_client_w_places.post(
#         "places/%s/update" % entry_id,
#         json={
#             "entry": {
#                 "code": 4,
#                 "name": "test3",
#                 "population": 5,
#                 "area": 50000,
#                 "density": 5,
#                 "municipality": [2, 3],
#             },
#             "message": "changes",
#             "version": 1,
#         },
#         headers={"Authorization": "Bearer 1234"},
#     )
#     response_data = response.json()
#     assert "newID" in response_data
#     assert "4" == response_data["newID"]

#     #     # check that the old entry with old id has been removed
#     #     entries = get_json(client, "places/query")
#     #     assert 1 == len(entries["hits"])
#     with unit_of_work(using=ctx.resource_repo) as uw:
#         resource = uw.by_resource_id("places")

#     with unit_of_work(using=resource.entry_repository) as uw:
#         resource_ids = uw.entry_ids()
#         assert "3" not in resource_ids
#         assert "4" in resource_ids


# def test_refs(es, client_with_data_f):
#     client = init(
#         client_with_data_f,
#         es,
#         [
#             {
#                 "code": 1,
#                 "name": "test1",
#                 "population": 10,
#                 "area": 50000,
#                 "density": 5,
#                 "municipality": [2, 3],
#             },
#             {
#                 "code": 2,
#                 "name": "test2",
#                 "population": 5,
#                 "larger_place": 1,
#                 "area": 50000,
#                 "density": 5,
#                 "municipality": [2, 3],
#             },
#         ],
#     )

#     entries = get_json(client, "places/query")
#     assert len(entries["hits"]) == 2
#     for val in entries["hits"]:
#         assert "entry" in val
#         entry = val["entry"]
#         print("entry = {}".format(entry))
#         if entry["code"] == 1:
#             assert "v_larger_place" not in entry
#             assert "larger_place" not in entry
#             assert "v_smaller_places" in entry
#             assert entry["v_smaller_places"][0]["code"] == 2
#         else:
#             assert entry["v_larger_place"]["code"] == 1
#             assert entry["v_larger_place"]["name"] == "test1"
#             assert "v_smaller_places" not in entry


# def test_external_refs(es, client_with_data_f):
#     client = init(
#         client_with_data_f,
#         es,
#         [
#             {
#                 "code": 1,
#                 "name": "test1",
#                 "population": 10,
#                 "area": 50000,
#                 "density": 5,
#                 "municipality": [1],
#             },
#             {
#                 "code": 2,
#                 "name": "test2",
#                 "population": 5,
#                 "larger_place": 1,
#                 "area": 50000,
#                 "density": 5,
#                 "municipality": [1, 2],
#             },
#             {
#                 "code": 3,
#                 "name": "test2",
#                 "population": 5,
#                 "larger_place": 1,
#                 "area": 50000,
#                 "density": 5,
#                 "municipality": [2],
#             },
#         ],
#     )

#     client.post(
#         "municipalities/add",
#         data=json.dumps(
#             {
#                 "entry": {
#                     "code": 1,
#                     "name": "municipality1",
#                     "state": "state1",
#                     "region": "region1",
#                 }
#             }
#         ),
#         content_type="application/json",
#     )

#     client.post(
#         "municipalities/add",
#         data=json.dumps(
#             {
#                 "entry": {
#                     "code": 2,
#                     "name": "municipality2",
#                     "state": "state2",
#                     "region": "region2",
#                 }
#             }
#         ),
#         content_type="application/json",
#     )

#     entries = get_json(client, "municipalities/query")
#     for val in entries["hits"]:
#         assert "entry" in val
#         entry = val["entry"]

#         assert "v_places" in entry
#         place_codes = [place["code"] for place in entry["v_places"]]
#         assert len(place_codes) == 2
#         if entry["code"] == 1:
#             assert 1 in place_codes
#             assert 2 in place_codes
#         else:
#             assert 2 in place_codes
#             assert 3 in place_codes

#     places_entries = get_json(client, "places/query")
#     for val in places_entries["hits"]:
#         assert "entry" in val
#         entry = val["entry"]
#         assert "municipality" in entry
#         assert isinstance(entry["v_municipality"], list)
#         if entry["code"] == 2:
#             assert {"code": 1, "name": "municipality1", "state": "state1"} in entry[
#                 "v_municipality"
#             ]
#             assert {"code": 2, "name": "municipality2", "state": "state2"} in entry[
#                 "v_municipality"
#             ]


# def test_update_refs(es, client_with_data_f):
#     client = init(
#         client_with_data_f,
#         es,
#         [
#             {
#                 "code": 5,
#                 "name": "test1",
#                 "population": 10,
#                 "area": 50000,
#                 "density": 5,
#                 "municipality": [2, 3],
#             },
#             {
#                 "code": 6,
#                 "name": "test2",
#                 "population": 5,
#                 "larger_place": 5,
#                 "area": 50000,
#                 "density": 5,
#                 "municipality": [2, 3],
#             },
#         ],
#     )

#     entries = get_json(client, "places/query")
#     assert len(entries["hits"]) == 2
#     for val in entries["hits"]:
#         assert "entry" in val
#         entry = val["entry"]
#         print("entry = {}".format(entry))
#         if entry["code"] == 5:
#             assert "v_smaller_places" in entry
#             assert entry["v_smaller_places"][0]["code"] == 6

#     client.delete("/places/6/delete")

#     entries = get_json(client, "places/query")
#     assert len(entries["hits"]) == 1
#     entry = entries["hits"][0]
#     assert "v_smaller_places" not in entry


# def test_update_refs2(es, client_with_data_f):
#     client = init(
#         client_with_data_f, es, [{"code": 3, "name": "test3", "municipality": [2, 3]}]
#     )

#     client.post(
#         "places/3/update",
#         data=json.dumps(
#             {
#                 "entry": {"code": 3, "name": "test3", "municipality": [2]},
#                 "message": "changes",
#                 "version": 1,
#             }
#         ),
#         content_type="application/json",
#     )

#     entries = get_json(client, "places/query")
#     assert len(entries["hits"]) == 1
#     assert entries["hits"][0]["id"] == "3"
#     assert entries["hits"][0]["entry"]["municipality"] == [2]
#     assert (
#         "v_municipality" not in entries["hits"][0]
#         or len(entries["hits"][0]["municipality"]) == 0
#     )
#     with client.application.app_context():
#         db_entry = entryread.get_entry("places", "3")
#         assert len(db_entry.municipality) == 1
#         assert db_entry.municipality[0].municipality == 2


# def test_last_modified(es, client_with_data_f):
#     before_add = datetime.now(timezone.utc).timestamp()

#     time.sleep(1)
#     client = init(
#         client_with_data_f, es, [{"code": 1, "name": "test1", "municipality": [1]}]
#     )
#     time.sleep(1)

#     after_add = datetime.now(timezone.utc).timestamp()

#     entries = get_json(client, "places/query")
#     hit = entries["hits"][0]
#     assert "dummy" == hit["last_modified_by"]
#     assert before_add < hit["last_modified"]
#     assert after_add > hit["last_modified"]

#     time.sleep(1)
#     client.post(
#         "places/1/update",
#         data=json.dumps(
#             {
#                 "entry": {"code": 1, "name": "test2", "municipality": [1]},
#                 "message": "changes",
#                 "version": 1,
#             }
#         ),
#         content_type="application/json",
#     )
#     time.sleep(1)

#     after_update = datetime.now(timezone.utc).timestamp()

#     entries = get_json(client, "places/query")
#     hit = entries["hits"][0]
#     assert "dummy" == hit["last_modified_by"]
#     assert after_add < hit["last_modified"]
#     assert after_update > hit["last_modified"]
