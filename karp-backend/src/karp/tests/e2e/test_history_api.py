# import json
import re  # noqa: I001
import time
from karp.lex.domain.entities import EntryOp

import pytest  # pyre-ignore
from starlette import status

from karp import auth
from karp.foundation.time import utc_now
from karp.lex.application.queries.entries import (
    EntryDiffDto,
    EntryDto,
    GetHistoryDto,
    HistoryDto,  # noqa: F401
)

places = [
    {"code": 103, "name": "a", "municipality": [1]},
    {"code": 104, "name": "b", "municipality": [2, 3]},
    {"code": 105, "name": "c", "municipality": [2, 3], "larger_place": 4},
    {"code": 106, "name": "c", "municipality": [1], "larger_place": 5},
]


def get_helper(client, url: str, access_token: auth.AccessToken) -> dict:
    response = client.get(
        url,
        headers=access_token.as_header(),
    )
    assert response.status_code == status.HTTP_200_OK
    return response.json()


def username(name: str) -> str:
    return f"{__name__}-{name}"


@pytest.fixture(name="history_entity_ids", scope="session")
def fixture_history_entity_ids(
    fa_data_client,
    user1_token: auth.AccessToken,
    user2_token: auth.AccessToken,
    user4_token: auth.AccessToken,
) -> list[str]:
    entity_ids = []
    for entry in places[:2]:
        response = fa_data_client.post(
            "/entries/places/add",
            json={"entry": entry, "message": "Add it"},
            headers=user1_token.as_header(),
        )
        print(f"{response.json()=}")
        assert response.status_code == status.HTTP_201_CREATED
        entity_ids.append(response.json()["newID"])
        time.sleep(1)

    for entry in places[2:]:
        response = fa_data_client.post(
            "/entries/places/add",
            json={"entry": entry, "message": "Add it"},
            headers=user2_token.as_header(),
        )
        assert response.status_code == status.HTTP_201_CREATED
        entity_ids.append(response.json()["newID"])
        time.sleep(1)

    for i, entry in enumerate(places[:2]):
        changed_entry = entry.copy()
        changed_entry["name"] = entry["name"] + entry["name"]
        fa_data_client.post(
            f"/entries/places/{entity_ids[i]}/update",
            json={"entry": changed_entry, "message": "change it", "version": 1},
            headers=user2_token.as_header(),
        )
        time.sleep(1)

    for i, entry in enumerate(places[2:], start=2):
        changed_entry = entry.copy()
        changed_entry["name"] = entry["name"] + entry["name"]
        fa_data_client.post(
            f"/entries/places/{entity_ids[i]}/update",
            json={"entry": changed_entry, "message": "change it", "version": 1},
            headers=user1_token.as_header(),
        )
        time.sleep(1)

    diff_entry_id = entity_ids[0]
    for i in range(3, 10):
        changed_entry = places[0].copy()
        changed_entry["name"] = places[0]["name"] * i
        response = fa_data_client.post(
            f"/entries/places/{diff_entry_id}/update",
            json={"entry": changed_entry, "message": "changes", "version": i - 1},
            headers=user4_token.as_header(),
        )
        print(f"response = {response.json()}")
        assert response.status_code == status.HTTP_200_OK
        time.sleep(1)
    return entity_ids


class TestGetHistory:
    def test_route_exist(self, fa_data_client):  # noqa: ANN201
        response = fa_data_client.get("/history/places")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_empty_user_history(  # noqa: ANN201
        self,
        fa_data_client,
        admin_token: auth.AccessToken,
        history_entity_ids: list[str],
    ):
        response_data = get_helper(
            fa_data_client, "/history/places?user_id=user3", admin_token
        )
        assert len(response_data["history"]) == 0
        assert response_data["total"] == 0

    def test_user1_history(  # noqa: ANN201
        self,
        fa_data_client,
        admin_token: auth.AccessToken,
        history_entity_ids: list[str],
    ):
        response_data = get_helper(
            fa_data_client,
            "/history/places?user_id=user1",
            admin_token,
        )
        history = GetHistoryDto(**response_data)
        assert len(history.history) == 4
        assert history.total == 4
        for history_entry in history.history:
            assert "user1" == history_entry.user_id

    def test_user2_history(  # noqa: ANN201
        self,
        fa_data_client,
        admin_token: auth.AccessToken,
        history_entity_ids: list[str],
    ):
        response_data = get_helper(
            fa_data_client,
            "/history/places?user_id=user2",
            admin_token,
        )
        history = GetHistoryDto(**response_data)
        assert len(history.history) == 4
        print(f"{history=}")
        assert history.history[0].op == EntryOp.ADDED
        assert history.history[1].op == EntryOp.ADDED
        assert history.history[2].op == EntryOp.UPDATED
        assert history.history[3].op == EntryOp.UPDATED
        assert re.match(r"^\d{10}\.\d{3,6}$", str(history.history[3].timestamp))
        for history_entry in history.history:
            assert history_entry.user_id == "user2"

    def test_user_history_from_date(  # noqa: ANN201
        self,
        fa_data_client,
        admin_token: auth.AccessToken,
        history_entity_ids: list[str],
    ):
        response_data = get_helper(
            fa_data_client,
            f"/history/places?user_id=user1&from_date={utc_now() - 5}",
            admin_token,
        )
        assert 4 > len(response_data["history"]), len(response_data["history"])

    def test_user_history_to_date(  # noqa: ANN201
        self,
        fa_data_client,
        admin_token: auth.AccessToken,
        history_entity_ids: list[str],
    ):
        response_data = get_helper(
            fa_data_client,
            f"/history/places?user_id=user2&to_date={utc_now() - 5}",
            admin_token,
        )
        assert len(response_data["history"]) == 4

    def test_entry_id(  # noqa: ANN201
        self,
        fa_data_client,
        admin_token: auth.AccessToken,
        history_entity_ids: list[str],
    ):
        response_data = get_helper(
            fa_data_client,
            f"/history/places?entry_id={history_entity_ids[1]}",
            admin_token,
        )
        history = GetHistoryDto(**response_data)
        assert len(history.history) == 2
        for history_entry in history.history:
            assert history_entry.id == history_entity_ids[1]

    def test_entry_id_and_user_id(  # noqa: ANN201
        self,
        fa_data_client,
        admin_token: auth.AccessToken,
        history_entity_ids: list[str],
    ):
        response_data = get_helper(
            fa_data_client,
            f"/history/places?entry_id={history_entity_ids[0]}&user_id=user2",
            admin_token,
        )
        history = GetHistoryDto(**response_data)
        assert len(history.history) == 1
        history_entry = history.history[0]
        assert history_entry.id == history_entity_ids[0]
        assert history_entry.user_id == "user2"
        assert history_entry.op == EntryOp.UPDATED

    def test_diff_against_nothing(  # noqa: ANN201
        self,
        fa_data_client,
        admin_token: auth.AccessToken,
        history_entity_ids: list[str],
    ):
        response_data = get_helper(
            fa_data_client,
            f"/history/places?entry_id={history_entity_ids[0]}&to_version=2",
            admin_token,
        )
        history = GetHistoryDto(**response_data)
        assert len(history.history) == 1
        history_entry = history.history[0]
        assert EntryOp.ADDED == history_entry.op
        for diff in history_entry.diff:
            print(f"diff = {diff}")
            assert diff["type"] == "ADDED"


def test_historical_entry(  # noqa: ANN201
    fa_data_client,
    admin_token: auth.AccessToken,
    history_entity_ids: list[str],
):
    response_json = get_helper(
        fa_data_client,
        f"/entries/places/{history_entity_ids[1]}/2",
        admin_token,
    )
    history_entry = EntryDto(**response_json)
    assert history_entry.last_modified < utc_now()
    assert history_entry.last_modified_by == "user2"
    # assert "resource" in response_data
    assert history_entry.entry["name"] == "bb"
    # assert "version" in response_data
    assert history_entry.version == 2


class TestGetEntryDiff:
    def test_diff1(  # noqa: ANN201
        self,
        fa_data_client,
        user4_token: auth.AccessToken,
        history_entity_ids: list[str],
    ):
        response = fa_data_client.post(
            f"/history/diff/places/{history_entity_ids[0]}?from_version=1&to_version=2",
            headers=user4_token.as_header(),
        )
        assert response.status_code == status.HTTP_200_OK
        response_data = EntryDiffDto(**response.json())

        assert len(response_data.diff) == 1
        assert response_data.diff[0]["type"] == "CHANGE"
        assert response_data.diff[0]["before"] == "a"
        assert response_data.diff[0]["after"] == "aa"
        assert response_data.diff[0]["field"] == "name"
        assert response_data.from_version == 1
        assert response_data.to_version == 2

    def test_diff2(  # noqa: ANN201
        self,
        fa_data_client,
        user4_token: auth.AccessToken,
        history_entity_ids: list[str],
    ):
        response = fa_data_client.post(
            f"/history/diff/places/{history_entity_ids[0]}?from_date=0&to_date={utc_now()}",
            headers=user4_token.as_header(),
        )
        assert response.status_code == status.HTTP_200_OK
        response_data = EntryDiffDto(**response.json())
        assert response_data.diff[0]["before"] == "a"
        assert response_data.diff[0]["after"] == "aaaaaaaaa"
        assert response_data.from_version == 1
        assert response_data.to_version == 9

    def test_diff_from_first_to_date(  # noqa: ANN201
        self,
        fa_data_client,
        user4_token: auth.AccessToken,
        history_entity_ids: list[str],
    ):
        """
        this test is a bit shaky due to assuming that we will find the correct version by subtracting three seconds
        """
        response = fa_data_client.post(
            f"/history/diff/places/{history_entity_ids[0]}?to_date={utc_now() - 3}",
            headers=user4_token.as_header(),
        )
        assert response.status_code == status.HTTP_200_OK
        response_data = EntryDiffDto(**response.json())
        assert response_data.diff[0]["before"] == "a"
        assert response_data.diff[0]["after"] > "aaaaaa"
        assert response_data.from_version == 1
        assert response_data.to_version is not None
        assert response_data.to_version > 6

    @pytest.mark.xfail()
    def test_diff_from_date_to_last(  # noqa: ANN201
        self,
        fa_data_client,
        user4_token: auth.AccessToken,
        history_entity_ids: list[str],
    ):
        """
        this test is a bit shaky due to assuming that we will find the correct version by subtracting three seconds
        """
        response = fa_data_client.post(
            f"/history/diff/places/{history_entity_ids[0]}?from_date={utc_now() - 3}",
            headers=user4_token.as_header(),
        )
        assert response.status_code == status.HTTP_200_OK
        response_data = EntryDiffDto(**response.json())
        assert response_data.diff[0]["before"] == "aaaaaaaa"
        assert response_data.diff[0]["after"] == "aaaaaaaaa"
        assert response_data.from_version == 8
        assert response_data.to_version == 9

    def test_diff_from_first_to_version(  # noqa: ANN201
        self,
        fa_data_client,
        user4_token: auth.AccessToken,
        history_entity_ids: list[str],
    ):
        response = fa_data_client.post(
            f"/history/diff/places/{history_entity_ids[0]}?to_version=7",
            headers=user4_token.as_header(),
        )
        assert response.status_code == status.HTTP_200_OK
        response_data = EntryDiffDto(**response.json())
        assert response_data.diff[0]["before"] == "a"
        assert response_data.diff[0]["after"] == "aaaaaaa"
        assert response_data.from_version == 1
        assert response_data.to_version == 7

    def test_diff_from_version_to_last(  # noqa: ANN201
        self,
        fa_data_client,
        user4_token: auth.AccessToken,
        history_entity_ids: list[str],
    ):
        response = fa_data_client.post(
            f"/history/diff/places/{history_entity_ids[0]}?from_version=7",
            headers=user4_token.as_header(),
        )
        assert response.status_code == status.HTTP_200_OK
        response_data = EntryDiffDto(**response.json())
        assert response_data.diff[0]["before"] == "aaaaaaa"
        assert response_data.diff[0]["after"] == "aaaaaaaaa"
        assert response_data.from_version == 7
        assert response_data.to_version == 9

    def test_diff_mix_version_date(  # noqa: ANN201
        self,
        fa_data_client,
        user4_token: auth.AccessToken,
        history_entity_ids: list[str],
    ):
        response = fa_data_client.post(
            f"/history/diff/places/{history_entity_ids[0]}?from_version=2&to_date={utc_now() - 3}",
            headers=user4_token.as_header(),
        )
        assert response.status_code == status.HTTP_200_OK
        response_data = EntryDiffDto(**response.json())
        assert response_data.diff[0]["before"] == "aa"
        assert response_data.diff[0]["after"] > "aaaaaa"
        assert response_data.from_version == 2
        assert response_data.to_version is not None
        assert response_data.to_version > 6

    def test_diff_to_entry_data(  # noqa: ANN201
        self,
        fa_data_client,
        user4_token: auth.AccessToken,
        history_entity_ids: list[str],
    ):
        edited_entry = places[0].copy()
        edited_entry["name"] = "testing"
        response = fa_data_client.post(
            f"/history/diff/places/{history_entity_ids[0]}?from_version=1",
            json=edited_entry,
            headers=user4_token.as_header(),
        )
        assert response.status_code == status.HTTP_200_OK
        response_data = EntryDiffDto(**response.json())
        assert response_data.diff[0]["before"] == "a"
        assert response_data.diff[0]["after"] == "testing"
        assert response_data.from_version == 1
        assert response_data.to_version is None

    def test_diff_no_flags(  # noqa: ANN201
        self,
        fa_data_client,
        user4_token: auth.AccessToken,
        history_entity_ids: list[str],
    ):
        response = fa_data_client.post(
            f"/history/diff/places/{history_entity_ids[0]}?from_version=1",
            headers=user4_token.as_header(),
        )
        assert response.status_code == status.HTTP_200_OK
        response_data = EntryDiffDto(**response.json())

        assert response_data.diff[0]["before"] == "a"
        assert response_data.diff[0]["after"] == "aaaaaaaaa"
        assert response_data.from_version == 1
        assert response_data.to_version == 9
