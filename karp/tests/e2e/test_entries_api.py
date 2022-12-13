from typing import Dict, List
import uuid

import pytest  # pyre-ignore
from fastapi import status

from karp import auth
from karp.errors import ClientErrorCodes
from karp.lex.application.queries.resources import GetEntryRepositoryId
from karp.lex.application.repositories.entry_repositories import (
    EntryUowRepositoryUnitOfWork,
)
from karp.foundation.time import utc_now
from karp.foundation.value_objects import make_unique_id, UniqueId, unique_id
from karp.lex.application.queries import EntryDto

# from karp.application import ctx, config
# from karp.infrastructure.unit_of_work import unit_of_work


# from tests.utils import get_json

# from tests.integration_tests.common_fixtures import (
#     fixture_fa_data_client,
#     fixture_places,
# )


def get_entry_uow(container, resource_id: str):
    get_entry_repository_id = container.get(GetEntryRepositoryId)  # type: ignore [misc]
    entry_repo_id = get_entry_repository_id.query("places")
    entry_uow_repo_uow = container.get(EntryUowRepositoryUnitOfWork)  # type: ignore [misc]
    with entry_uow_repo_uow as uw:
        return uw.repo.get_by_id(entry_repo_id)


def init(
    client,
    entries: List[Dict],
    access_token: auth.AccessToken,
) -> list[str]:

    result = []
    for entry in entries:
        response = client.post(
            "/entries/places/add",
            json={"entry": entry},
            headers=access_token.as_header(),
        )
        assert response.status_code < 300, response.status_code
        result.append(response.json()["newID"])
    return result


@pytest.fixture(name="entry_places_214_id", scope="session")
def fixture_entry_places_214_id(
    fa_data_client,
    write_token: auth.AccessToken,
):

    ids = init(
        fa_data_client,
        [
            {"code": 214, "name": "last_modified1", "municipality": [1]},
        ],
        write_token,
    )
    return ids[0]


@pytest.fixture(name="entry_places_209_id", scope="session")
def fixture_entry_places_209_id(
    fa_data_client,
    write_token: auth.AccessToken,
):

    ids = init(
        fa_data_client,
        [
            {"code": 209, "name": "a", "municipality": [1]},
        ],
        write_token,
    )
    return ids[0]


class TestEntriesRoutes:
    def test_routes_exist(self, fa_data_client):
        response = fa_data_client.post("/entries/places/add")
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = fa_data_client.post("/entries/places/update")
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = fa_data_client.put("/entries/places")
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = fa_data_client.post("/entries/places/preview")
        assert response.status_code != status.HTTP_404_NOT_FOUND


class TestAddEntry:
    def test_put_route_exist(self, fa_data_client):
        response = fa_data_client.put("/entries/places")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize(
        "invalid_data",
        [
            ({},),
            ({"user": "a@b.se"},),
        ],
    )
    def test_invalid_data_returns_422(
        self,
        fa_data_client,
        invalid_data: Dict,
        write_token: auth.AccessToken,
    ):
        response = fa_data_client.post(
            "/entries/places/add",
            json=invalid_data,
            headers=write_token.as_header(),
        )
        print(f"{response.json()=}")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_add_with_valid_data_returns_201(
        self,
        fa_data_client,
        write_token: auth.AccessToken,
    ):

        response = fa_data_client.put(
            "/entries/places",
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
            headers=write_token.as_header(),
        )
        print(f"response. = {response.json()}")
        assert response.status_code == 201
        response_data = response.json()
        assert "newID" in response_data
        new_id = unique_id.parse(response_data["newID"])

        entry_uow = get_entry_uow(
            fa_data_client.app.state.app_context.container, resource_id="places"
        )
        with entry_uow as uw:
            assert new_id in uw.repo.entity_ids()

    def test_add_with_valid_data_and_entity_id_returns_201(
        self,
        fa_data_client,
        write_token: auth.AccessToken,
    ):
        entity_id = make_unique_id()
        response = fa_data_client.put(
            "/entries/places",
            json={
                "entry": {
                    "code": 2078,
                    "name": "add203",
                    "population": 4,
                    "area": 50000,
                    "density": 5,
                    "municipality": [2, 3],
                },
                "id": str(entity_id),
            },
            headers=write_token.as_header(),
        )
        print(f"response. = {response.json()}")
        assert response.status_code == 201
        response_data = response.json()
        assert "newID" in response_data
        new_id = response_data["newID"]

        entry_uow = get_entry_uow(
            fa_data_client.app.state.app_context.container, resource_id="places"
        )
        with entry_uow as uw:
            assert new_id in uw.repo.entity_ids()

    @pytest.mark.skip(reason="we don't use entry_id")
    def test_adding_existing_fails_with_400(
        self,
        fa_data_client,
        write_token: auth.AccessToken,
    ):
        entry_id = 204
        entry_name = f"add{entry_id}"
        response = fa_data_client.post(
            "/entries/places/add",
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
            headers=write_token.as_header(),
        )
        print(f"response = {response.json()}")

        assert response.status_code == 201

        response = fa_data_client.post(
            "/entries/places/add",
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
            headers=write_token.as_header(),
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

    def test_add_fails_with_invalid_entry(
        self,
        fa_data_client,
        write_token: auth.AccessToken,
    ):
        response = fa_data_client.post(
            "/entries/places/add", json={"entry": {}}, headers=write_token.as_header()
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data["errorCode"] == ClientErrorCodes.ENTRY_NOT_VALID

        # assert (
        #     response_data["error"] == "Missing ID field for resource 'places' in '{}'"
        # )


class TestDeleteEntry:
    def test_delete(
        self,
        fa_data_client,
        write_token: auth.AccessToken,
    ):
        entry_id = 205
        entry_name = f"delete{entry_id}"
        response = fa_data_client.post(
            "/entries/places/add",
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
            headers=write_token.as_header(),
        )

        entity_id = response.json()["newID"]
        response = fa_data_client.delete(
            f"/entries/places/{entity_id}/delete", headers=write_token.as_header()
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        entry_uow = get_entry_uow(
            fa_data_client.app.state.app_context.container, resource_id="places"
        )
        with entry_uow as uw:
            assert uw.repo.by_id(entity_id).discarded
            assert entity_id not in uw.repo.entity_ids()

    def test_delete_rest(
        self,
        fa_data_client,
        write_token: auth.AccessToken,
    ):
        entry_id = 205
        entry_name = f"delete{entry_id}"
        response = fa_data_client.put(
            "/entries/places",
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
            headers=write_token.as_header(),
        )

        entity_id = response.json()["newID"]
        response = fa_data_client.delete(
            f"/entries/places/{entity_id}", headers=write_token.as_header()
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        entry_uow = get_entry_uow(
            fa_data_client.app.state.app_context.container, resource_id="places"
        )
        with entry_uow as uw:
            assert uw.repo.by_id(entity_id).discarded
            assert entity_id not in uw.repo.entity_ids()

    def test_delete_non_existing_fails(
        self,
        fa_data_client,
        write_token: auth.AccessToken,
    ):

        entry_id = make_unique_id()

        response = fa_data_client.delete(
            f"/entries/places/{entry_id}/delete", headers=write_token.as_header()
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

        response_data = response.json()

        assert response_data["errorCode"] == ClientErrorCodes.ENTRY_NOT_FOUND

        assert (
            response_data["error"]
            == f"Entry '{entry_id}' not found in resource 'places' (version=latest)"
        )

    def test_delete_rest_non_existing_fails(
        self,
        fa_data_client,
        write_token: auth.AccessToken,
    ):

        entry_id = "00000000000000000000000000"

        response = fa_data_client.delete(
            f"/entries/places/{entry_id}", headers=write_token.as_header()
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

        response_data = response.json()

        assert response_data["errorCode"] == ClientErrorCodes.ENTRY_NOT_FOUND

        assert (
            response_data["error"]
            == f"Entry '{entry_id}' not found in resource 'places' (version=latest)"
        )


class TestUpdateEntry:
    def test_update_non_existing_fails(
        self,
        fa_data_client,
        write_token: auth.AccessToken,
    ):
        entry_id = make_unique_id()
        response = fa_data_client.post(
            f"/entries/places/{entry_id}/update",
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
            headers=write_token.as_header(),
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_data = response.json()
        assert response_data["errorCode"] == ClientErrorCodes.ENTRY_NOT_FOUND

        assert (
            response_data["error"]
            == f"Entry '{entry_id}' not found in resource 'places' (version=latest)"
        )

    def test_update_wo_changes_succeeds(
        self,
        fa_data_client,
        write_token: auth.AccessToken,
    ):
        entry_id = 206
        entry_name = f"update{entry_id}"
        response = fa_data_client.post(
            "/entries/places/add",
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
            headers=write_token.as_header(),
        )
        print(f"response = {response.json()}")
        entity_id = response.json()["newID"]
        assert response.status_code == status.HTTP_201_CREATED

        response = fa_data_client.post(
            f"/entries/places/{entity_id}/update",
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
            headers=write_token.as_header(),
        )
        assert response.status_code == status.HTTP_200_OK

    def test_update_wrong_version_fails(
        self,
        fa_data_client,
        write_token: auth.AccessToken,
    ):
        entry_id = 207
        response = fa_data_client.post(
            "/entries/places/add",
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
            headers=write_token.as_header(),
        )
        print(f"response = {response.json()}")
        entity_id = response.json()["newID"]

        assert response.status_code == 201

        response = fa_data_client.post(
            f"/entries/places/{entity_id}/update",
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
            headers=write_token.as_header(),
            #         ),
            #         content_type='application/json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data["errorCode"] == ClientErrorCodes.VERSION_CONFLICT

        assert response_data["error"] == "Version conflict. Please update entry."
        assert response_data["diff"] == [
            {"type": "CHANGE", "field": "population", "before": 4, "after": 5}
        ]

    def test_update_returns_200_on_valid_data(
        self,
        fa_data_client,
        write_token: auth.AccessToken,
    ):
        entry_id = 208
        entry_name = f"update{entry_id}"
        response = fa_data_client.post(
            "/entries/places/add",
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
            headers=write_token.as_header(),
        )
        print(f"response = {response.json()}")
        entity_id = response.json()["newID"]

        assert response.status_code == status.HTTP_201_CREATED

        response = fa_data_client.post(
            f"/entries/places/{entity_id}/update",
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
            headers=write_token.as_header(),
        )
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["newID"] == entity_id

        entry_uow = get_entry_uow(
            fa_data_client.app.state.app_context.container, resource_id="places"
        )
        with entry_uow as uw:
            assert uw.repo.by_id(entity_id).body["population"] == 5
            assert entity_id in uw.repo.entity_ids()

    def test_update_several_times(
        self,
        fa_data_client,
        write_token: auth.AccessToken,
        entry_places_209_id: str,
    ):
        entry_id = 209

        entity_id = entry_places_209_id

        for i in range(2, 10):
            response = fa_data_client.post(
                f"/entries/places/{entity_id}/update",
                json={
                    "entry": {"code": entry_id, "name": "a" * i, "municipality": [1]},
                    "message": "changes",
                    "version": i - 1,
                },
                headers=write_token.as_header(),
            )
            print(f"i = {i}: response = {response.json()}")
            assert response.status_code == status.HTTP_200_OK

    @pytest.mark.xfail()
    def test_update_entry_id(
        self,
        fa_data_client,
        write_token: auth.AccessToken,
    ):
        entry_id = 210
        response = fa_data_client.post(
            "/entries/places/add",
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
            headers=write_token.as_header(),
        )
        assert response.status_code == 201

        response = fa_data_client.post(
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
            headers=write_token.as_header(),
        )
        response_data = response.json()
        print(f"{response.json()=}")
        assert str(entry_id + 1) == response_data["newID"]

        entry_uow = get_entry_uow(
            fa_data_client.app.state.app_context.container, resource_id="places"
        )
        with entry_uow as uw:
            entry_ids = uw.repo.entry_ids()
            assert str(entry_id) not in entry_ids
            assert str(entry_id + 1) in entry_ids

    def test_update_changes_last_modified(
        self,
        fa_data_client,
        write_token: auth.AccessToken,
    ):
        entry_id = 212
        before_add = utc_now()

        ids = init(
            fa_data_client,
            [
                {"code": entry_id, "name": "last_modified1", "municipality": [1]},
            ],
            write_token,
        )

        after_add = utc_now()

        entry_uow = get_entry_uow(
            fa_data_client.app.state.app_context.container, resource_id="places"
        )
        entity_id = ids[0]
        with entry_uow as uw:
            entry = uw.repo.by_id(entity_id)
            assert entry.last_modified > before_add
            assert entry.last_modified < after_add

        fa_data_client.post(
            f"/entries/places/{entity_id}/update",
            json={
                "entry": {
                    "code": entry_id,
                    "name": "last_modified2",
                    "municipality": [1],
                },
                "message": "changes",
                "version": 1,
            },
            headers=write_token.as_header(),
        )

        after_update = utc_now()

        with entry_uow as uw:
            entry = uw.repo.by_id(entity_id)
            assert entry.last_modified > after_add
            assert entry.last_modified < after_update


class TestGetEntry:
    def test_get_entry_wo_auth_returns_403(
        self, fa_data_client, entry_places_214_id: str
    ):
        response = fa_data_client.get(f"/entries/places/{entry_places_214_id}")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_entry_w_lower_auth_returns_401(
        self,
        fa_data_client,
        write_token: auth.AccessToken,
        entry_places_214_id: str,
    ):
        response = fa_data_client.get(
            f"/entries/places/{entry_places_214_id}",
            headers=write_token.as_header(),
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_entry_by_entry_id(
        self,
        fa_data_client,
        admin_token: auth.AccessToken,
        entry_places_214_id: str,
    ):
        response = fa_data_client.get(
            f"/entries/places/{entry_places_214_id}",
            headers=admin_token.as_header(),
        )
        assert response.status_code == status.HTTP_200_OK

        entry = EntryDto(**response.json())
        assert entry.entity_id == entry_places_214_id
        assert entry.version == 1

    def test_route_w_version_exist(
        self,
        fa_data_client,
        admin_token: auth.AccessToken,
        entry_places_209_id: str,
    ):
        response = fa_data_client.get(
            f"/entries/places/{entry_places_209_id}/5",
            headers=admin_token.as_header(),
        )
        assert response.status_code == status.HTTP_200_OK

        entry = EntryDto(**response.json())
        assert entry.entity_id == entry_places_209_id
        assert entry.version == 5


class TestPreviewEntry:
    def test_preview_fails_with_422_on_invalid_data(
        self, fa_data_client, read_token: auth.AccessToken
    ):
        response = fa_data_client.post(
            "/entries/places/preview", json={}, headers=read_token.as_header()
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_preview_returns_200_on_valid_data(
        self, fa_data_client, read_token: auth.AccessToken
    ):
        response = fa_data_client.post(
            "/entries/places/preview",
            json={
                "entry": {
                    "code": 3,
                    "name": "update3",
                    "population": 4,
                    "area": 50000,
                    "density": 5,
                    "municipality": [2, 3],
                },
                "message": "test",
            },
            headers=read_token.as_header(),
        )
        print(f"{response.json()=}")
        assert response.status_code == status.HTTP_200_OK
        assert unique_id.parse(response.json()["entry"]["id"])


@pytest.mark.skip()
def test_update_wrong_id(fa_data_client, write_token: auth.AccessToken):
    response = fa_data_client.post(
        "/entries/places/add",
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
        headers=write_token.as_header(),
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

    response = fa_data_client.post(
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
        headers=write_token.as_header(),
    )
    assert response.status_code == 400
    response_data = response.json()
    assert response_data["errorCode"] == ClientErrorCodes.ENTRY_ID_MISMATCH

    assert response_data["error"] == "entry_id '4' does not equal '3'"


@pytest.mark.skip()
def test_refs(fa_data_client):
    client = init(
        fa_data_client,
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
def test_external_refs(fa_data_client):
    client = init(
        fa_data_client,
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
def test_update_refs(fa_data_client):
    client = init(
        fa_data_client,
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
def test_update_refs2(fa_data_client):
    client = init(
        fa_data_client, es, [{"code": 3, "name": "test3", "municipality": [2, 3]}]
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
