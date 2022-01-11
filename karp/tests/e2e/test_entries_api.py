# import json
# import time
# from datetime import datetime, timezone
# from unittest import mock

import pytest  # pyre-ignore

# import karp.resourcemgr.entryread as entryread
from karp import config
from karp.errors import ClientErrorCodes
from karp.lex.application.queries.resources import GetEntryRepositoryId
from karp.lex.application.repositories.entry_repositories import EntryUowRepositoryUnitOfWork
from karp.utility.time import utc_now

# from karp.application import ctx, config
# from karp.infrastructure.unit_of_work import unit_of_work


# from tests.utils import get_json

# from tests.integration_tests.common_fixtures import (
#     fixture_fa_client,
#     fixture_places,
# )

def get_entry_uow(container, resource_id: str):
    get_entry_repository_id = container.get(GetEntryRepositoryId)
    entry_repo_id = get_entry_repository_id.query('places')
    entry_uow_repo_uow = container.get(EntryUowRepositoryUnitOfWork)
    with entry_uow_repo_uow as uw:
        return uw.repo.get_by_id(entry_repo_id)


def init(client, entries):

    for entry in entries:
        response = client.post(
            "places/add",
            json={"entry": entry},
            headers={"Authorization": "Bearer FAKETOKEN"},
        )
        assert response.status_code < 300, response.status_code
    return client


pytestmark = pytest.mark.usefixtures(
    "use_dummy_authenticator")  # , "use_main_index")


@pytest.mark.usefixtures("places_published")
@pytest.mark.usefixtures("main_db")
def test_add(fa_client, app):  # fa_client):
    # client = init(fa_client, es, [])

    response = fa_client.post(
        "places/add",
        json={
            "entry": {
                "code": 203,
                "name": "add203",
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
    assert response_data["newID"] == "203"

    entry_uow = get_entry_uow(app.state.container, resource_id='places')
    with entry_uow as uw:
        entries = uw.repo.entry_ids()
        assert len(entries) == 1
        assert entries[0] == "203"
    # entries = get_json(client, "places/query")
    # assert len(entries["hits"]) == 1
    # assert entries["hits"][0]["entry"]["name"] == "test3"


@pytest.mark.usefixtures("places_published")
@pytest.mark.usefixtures("main_db")
def test_adding_existing_fails(fa_client):
    #     client = init(fa_client, es, [])
    entry_id = 204
    entry_name = f"add{entry_id}"
    response = fa_client.post(
        "places/add",
        json={
            "entry": {
                "code": entry_id,
                "name": entry_name,
                "population": 4,
                "area": 50000,
                "density": 5,
                "municipality": [2, 3],
            }
        },
        headers={"Authorization": "Bearer 1234"},
    )
    print(f"response = {response.json()}")

    assert response.status_code == 201

    response = fa_client.post(
        "places/add",
        json={
            "entry": {
                "code": entry_id,
                "name": entry_name,
                "population": 4,
                "area": 50000,
                "density": 5,
                "municipality": [2, 3],
            }
        },
        headers={"Authorization": "Bearer 1234"},
    )
    assert response.status_code == 400
    response_data = response.json()

    assert "error" in response_data
    assert "errorCode" in response_data
    assert ClientErrorCodes.DB_INTEGRITY_ERROR == response_data["errorCode"]
    assert (
        response_data["error"]
        == f"An entry with entry_id '{entry_id}' already exists."
    )


@pytest.mark.usefixtures("places_published")
@pytest.mark.usefixtures("main_db")
def test_add_fails_with_invalid_entry(fa_client):
    response = fa_client.post(
        "/places/add", json={"entry": {}}, headers={"Authorization": "Bearer 1234"}
    )

    assert response.status_code == 400
    response_data = response.json()

    assert response_data["error"] == "Missing ID field for resource 'places' in '{}'"
    assert response_data["errorCode"] == ClientErrorCodes.ENTRY_NOT_VALID


@pytest.mark.usefixtures("places_published")
@pytest.mark.usefixtures("main_db")
def test_delete(fa_client, app):
    entry_id = 205
    entry_name = f"delete{entry_id}"
    response = fa_client.post(
        "places/add",
        json={
            "entry": {
                "code": entry_id,
                "name": entry_name,
                "population": 4,
                "area": 50000,
                "density": 5,
                "municipality": [2, 3],
            }
        },
        headers={"Authorization": "Bearer 1234"},
    )
    print(f"response = {response.json()}")

    assert response.status_code == 201

    entry_uow = get_entry_uow(app.state.container, resource_id='places')
    with entry_uow as uw:
        assert f"{entry_id}" in uw.repo.entry_ids()

    response = fa_client.delete(
        f"places/{entry_id}/delete", headers={"Authorization": "Bearer 1234"}
    )

    assert response.status_code == 200
    with entry_uow as uw:
        assert uw.repo.by_entry_id(str(entry_id)).discarded
        assert str(entry_id) not in uw.repo.entry_ids()


@pytest.mark.usefixtures("places_published")
@pytest.mark.usefixtures("main_db")
def test_delete_non_existing_fails(fa_client):

    entry_id = "non_existing_id"

    response = fa_client.delete(
        f"places/{entry_id}/delete", headers={"Authorization": "Bearer 1234"}
    )

    assert response.status_code == 404

    response_data = response.json()

    assert response_data["errorCode"] == ClientErrorCodes.ENTRY_NOT_FOUND

    assert (
        response_data["error"]
        == f"Entry '{entry_id}' not found in resource 'places' (version=latest)"
    )


@pytest.mark.usefixtures("places_published")
@pytest.mark.usefixtures("main_db")
def test_update_non_existing_fails(fa_client):
    entry_id = "non-existent"
    response = fa_client.post(
        f"/places/{entry_id}/update",
        json={
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
        },
        headers={"Authorization": "Bearer 1234"},
        #         ),
        #         content_type="application/json",
    )
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["errorCode"] == ClientErrorCodes.ENTRY_NOT_FOUND

    assert (
        response_data["error"]
        == f"Entry '{entry_id}' not found in resource 'places' (version=latest)"
    )


@pytest.mark.usefixtures("places_published")
@pytest.mark.usefixtures("main_db")
def test_update_wo_changes_succeeds(fa_client):
    entry_id = 206
    entry_name = f"update{entry_id}"
    response = fa_client.post(
        "places/add",
        json={
            "entry": {
                "code": entry_id,
                "name": entry_name,
                "population": 4,
                "area": 50000,
                "density": 5,
                "municipality": [2, 3],
            }
        },
        headers={"Authorization": "Bearer 1234"},
    )
    print(f"response = {response.json()}")

    assert response.status_code == 201

    response = fa_client.post(
        f"places/{entry_id}/update",
        json={
            "entry": {
                "code": entry_id,
                "name": entry_name,
                "population": 4,
                "area": 50000,
                "density": 5,
                "municipality": [2, 3],
            },
            "message": "changes",
            "version": 1,
        },
        headers={"Authorization": "Bearer 1234"},
        #         ),
        #         content_type="application/json",
    )
    assert response.status_code == 200


@pytest.mark.skip()
def test_update_wrong_id(fa_client):
    response = fa_client.post(
        "places/add",
        json={
            "entry": {
                "code": 3,
                "name": "update3",
                "population": 4,
                "area": 50000,
                "density": 5,
                "municipality": [2, 3],
            }
        },
        headers={"Authorization": "Bearer 1234"},
    )
    print(f"response = {response.json()}")

    assert response.status_code == 201
    entry_id = response.json()["newID"]

    with unit_of_work(using=ctx.resource_repo) as uw:
        resource = uw.get_active_resource("places")

    with unit_of_work(using=resource.entry_repository) as uw:
        entries = uw.entry_ids()
        assert len(entries) == 1
        assert entries[0] == "3"

    response = fa_client.post(
        f"places/{entry_id}/update",
        json={
            "entry": {
                "code": 4,
                "name": "update3",
                "population": 4,
                "area": 50000,
                "density": 5,
                "municipality": [2, 3],
            },
            "message": "changes",
            "version": 1,
        },
        headers={"Authorization": "Bearer 1234"},
        #         ),
        #         content_type="application/json",
    )
    assert response.status_code == 400
    response_data = response.json()
    assert response_data["errorCode"] == ClientErrorCodes.ENTRY_ID_MISMATCH

    assert response_data["error"] == "entry_id '4' does not equal '3'"


@pytest.mark.usefixtures("places_published")
@pytest.mark.usefixtures("main_db")
def test_update_wrong_version_fails(fa_client):
    entry_id = 207
    response = fa_client.post(
        "places/add",
        json={
            "entry": {
                "code": entry_id,
                "name": "update3",
                "population": 4,
                "area": 50000,
                "density": 5,
                "municipality": [2, 3],
            }
        },
        headers={"Authorization": "Bearer 1234"},
    )
    print(f"response = {response.json()}")

    assert response.status_code == 201

    response = fa_client.post(
        f"places/{entry_id}/update",
        json={
            "entry": {
                "code": entry_id,
                "name": "update3",
                "population": 5,
                "area": 50000,
                "density": 5,
                "municipality": [2, 3],
            },
            "message": "changes",
            "version": 2,
        },
        headers={"Authorization": "Bearer 1234"},
        #         ),
        #         content_type="application/json",
    )
    assert response.status_code == 400
    response_data = response.json()
    assert response_data["errorCode"] == ClientErrorCodes.VERSION_CONFLICT

    assert response_data["error"] == "Version conflict. Please update entry."
    assert response_data["diff"] == [
        {"type": "CHANGE", "field": "population", "before": 4, "after": 5}
    ]


@pytest.mark.usefixtures("places_published")
@pytest.mark.usefixtures("main_db")
def test_update(fa_client, app):
    entry_id = 208
    entry_name = f"update{entry_id}"
    response = fa_client.post(
        "places/add",
        json={
            "entry": {
                "code": entry_id,
                "name": entry_name,
                "population": 4,
                "area": 50000,
                "density": 5,
                "municipality": [2, 3],
            }
        },
        headers={"Authorization": "Bearer 1234"},
    )
    print(f"response = {response.json()}")

    assert response.status_code == 201

    response = fa_client.post(
        f"places/{entry_id}/update",
        json={
            "entry": {
                "code": entry_id,
                "name": entry_name,
                "population": 5,
                "area": 50000,
                "density": 5,
                "municipality": [2, 3],
            },
            "message": "changes",
            "version": 1,
        },
        headers={"Authorization": "Bearer 1234"},
        #         ),
        #         content_type="application/json",
    )
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["newID"] == str(entry_id)

    #     entries = get_json(client, "places/query")
    #     assert len(entries["hits"]) == 1
    #     assert entries["hits"][0]["id"] == entry_id
    #     assert entries["hits"][0]["entry"]["population"] == 5

    entry_uow = get_entry_uow(app.state.container, resource_id='places')
    with entry_uow as uw:
        assert uw.repo.by_entry_id(str(entry_id)).body["population"] == 5
        assert str(entry_id) in uw.repo.entry_ids()


@pytest.mark.usefixtures("places_published")
@pytest.mark.usefixtures("main_db")
def test_update_several_times(fa_client):
    entry_id = 209
    response = fa_client.post(
        "places/add",
        json={"entry": {"code": entry_id, "name": "a", "municipality": [1]}},
        headers={"Authorization": "Bearer 1234"},
    )
    assert response.status_code == 201
    for i in range(2, 10):
        response = fa_client.post(
            f"places/{entry_id}/update",
            json={
                "entry": {"code": entry_id, "name": "a" * i, "municipality": [1]},
                "message": "changes",
                "version": i - 1,
            },
            headers={"Authorization": "Bearer 1234"},
        )
        print(f"i = {i}: response = {response.json()}")
        assert response.status_code == 200


@pytest.mark.xfail()
@pytest.mark.usefixtures("places_published")
@pytest.mark.usefixtures("main_db")
def test_update_entry_id(fa_client, app):
    entry_id = 210
    response = fa_client.post(
        "places/add",
        json={
            "entry": {
                "code": entry_id,
                "name": "update3",
                "population": 4,
                "area": 50000,
                "density": 5,
                "municipality": [2, 3],
            }
        },
        headers={"Authorization": "Bearer 1234"},
    )
    assert response.status_code == 201

    response = fa_client.post(
        f"places/{entry_id}/update",
        json={
            "entry": {
                "code": entry_id + 1,
                "name": "update3",
                "population": 5,
                "area": 50000,
                "density": 5,
                "municipality": [2, 3],
            },
            "message": "changes",
            "version": 1,
        },
        headers={"Authorization": "Bearer 1234"},
    )
    response_data = response.json()
    print(f'{response.json()=}')
    assert str(entry_id + 1) == response_data["newID"]

    #     # check that the old entry with old id has been removed
    #     entries = get_json(client, "places/query")
    #     assert 1 == len(entries["hits"])
    entry_uow = get_entry_uow(app.state.container, resource_id='places')
    with entry_uow as uw:
        entry_ids = uw.repo.entry_ids()
        assert str(entry_id) not in entry_ids
        assert str(entry_id + 1) in entry_ids


@pytest.mark.skip()
@pytest.mark.usefixtures("places_published")
@pytest.mark.usefixtures("main_db")
def test_refs(fa_client):
    client = init(
        fa_client,
        [
            {
                "code": 1,
                "name": "refs1refs",
                "population": 10,
                "area": 50000,
                "density": 5,
                "municipality": [2, 3],
            },
            {
                "code": 2,
                "name": "refs2refs",
                "population": 5,
                "larger_place": 1,
                "area": 50000,
                "density": 5,
                "municipality": [2, 3],
            },
        ],
    )

    entries = get_json(client, "places/query")
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
            assert entry["v_larger_place"]["name"] == "refs1refs"
            assert "v_smaller_places" not in entry


@pytest.mark.skip()
@pytest.mark.usefixtures("places_published")
@pytest.mark.usefixtures("main_db")
def test_external_refs(es, fa_client):
    client = init(
        fa_client,
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

    entries = get_json(client, "municipalities/query")
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

    places_entries = get_json(client, "places/query")
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


@pytest.mark.skip()
@pytest.mark.usefixtures("places_published")
@pytest.mark.usefixtures("main_db")
def test_update_refs(es, fa_client):
    client = init(
        fa_client,
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

    entries = get_json(client, "places/query")
    assert len(entries["hits"]) == 2
    for val in entries["hits"]:
        assert "entry" in val
        entry = val["entry"]
        print("entry = {}".format(entry))
        if entry["code"] == 5:
            assert "v_smaller_places" in entry
            assert entry["v_smaller_places"][0]["code"] == 6

    client.delete("/places/6/delete")

    entries = get_json(client, "places/query")
    assert len(entries["hits"]) == 1
    entry = entries["hits"][0]
    assert "v_smaller_places" not in entry


@pytest.mark.skip()
@pytest.mark.usefixtures("places_published")
@pytest.mark.usefixtures("main_db")
def test_update_refs2(es, fa_client):
    client = init(fa_client, es, [
                  {"code": 3, "name": "test3", "municipality": [2, 3]}])

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

    entries = get_json(client, "places/query")
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


@pytest.mark.usefixtures("places_published")
@pytest.mark.usefixtures("main_db")
def test_last_modified(fa_client, app):
    entry_id = 212
    before_add = utc_now()

    # time.sleep(1)
    init(fa_client, [
         {"code": entry_id, "name": "last_modified1", "municipality": [1]}])
    # time.sleep(1)

    after_add = utc_now()

    entry_uow = get_entry_uow(app.state.container, resource_id='places')
    with entry_uow as uw:
        entry = uw.repo.by_entry_id(str(entry_id))
        assert entry.last_modified > before_add
        assert entry.last_modified < after_add
    # entries = get_json(client, "places/query")
    # hit = entries["hits"][0]
    # assert "dummy" == hit["last_modified_by"]
    # assert before_add < hit["last_modified"]
    # assert after_add > hit["last_modified"]

    fa_client.post(
        f"places/{entry_id}/update",
        json={
            "entry": {"code": entry_id, "name": "last_modified2", "municipality": [1]},
            "message": "changes",
            "version": 1,
        },
        headers={"Authorization": "Bearer 1234"},
    )

    after_update = utc_now()

    with entry_uow as uw:
        entry = uw.repo.by_entry_id(str(entry_id))
        assert entry.last_modified > after_add
        assert entry.last_modified < after_update
    # entries = get_json(client, "places/query")
    # hit = entries["hits"][0]
    # assert "dummy" == hit["last_modified_by"]
    # assert after_add < hit["last_modified"]
    # assert after_update > hit["last_modified"]
