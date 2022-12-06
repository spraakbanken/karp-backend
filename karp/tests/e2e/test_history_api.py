# import json
import re
import time
from datetime import datetime, timezone

import pytest  # pyre-ignore
from starlette import status

from karp import auth
from karp.foundation.time import utc_now
from karp.lex.application.queries.entries import EntryDto, GetHistoryDto, HistoryDto

places = [
    {"code": 103, "name": "a", "municipality": [1]},
    {"code": 104, "name": "b", "municipality": [2, 3]},
    {"code": 105, "name": "c", "municipality": [2, 3], "larger_place": 4},
    {"code": 106, "name": "c", "municipality": [1], "larger_place": 5},
]


def get_helper(client, url: str, access_token: auth.AccessToken):
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
    def test_route_exist(self, fa_data_client):
        response = fa_data_client.get("/history/places")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_empty_user_history(
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

    def test_user1_history(
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
        assert len(response_data["history"]) == 4
        assert response_data["total"] == 4
        for history_entry in response_data["history"]:
            assert "user1" == history_entry["user_id"]

    def test_user2_history(
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
        assert 4 == len(response_data["history"])
        assert response_data["history"][0]["op"] == "ADDED"
        assert response_data["history"][1]["op"] == "ADDED"
        assert "UPDATED" == response_data["history"][2]["op"]
        assert "UPDATED" == response_data["history"][3]["op"]
        assert re.match(
            r"^\d{10}\.\d{3,6}$", str(response_data["history"][3]["timestamp"])
        )
        for history_entry in response_data["history"]:
            assert "user2" == history_entry["user_id"]

    def test_user_history_from_date(
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

    def test_user_history_to_date(
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

    def test_entry_id(
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
        assert 2 == len(response_data["history"])
        for history_entry in response_data["history"]:
            assert history_entry["entity_id"] == history_entity_ids[1]

    def test_entry_id_and_user_id(
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
        assert 1 == len(response_data["history"])
        history_entry = response_data["history"][0]
        assert history_entry["entity_id"] == history_entity_ids[0]
        assert "user2" == history_entry["user_id"]
        assert "UPDATED" == history_entry["op"]

    def test_diff_against_nothing(
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
        assert 1 == len(response_data["history"])
        history_entry = response_data["history"][0]
        assert "ADDED" == history_entry["op"]
        for diff in history_entry["diff"]:
            print(f"diff = {diff}")
            assert "ADDED" == diff["type"]


def test_historical_entry(
    fa_data_client,
    admin_token: auth.AccessToken,
    history_entity_ids: list[str],
):
    response_data = get_helper(
        fa_data_client,
        f"/entries/places/{history_entity_ids[1]}/2",
        admin_token,
    )
    assert utc_now() > response_data["last_modified"]
    assert "user2" == response_data["last_modified_by"]
    assert "resource" in response_data
    assert "bb" == response_data["entry"]["name"]
    assert "version" in response_data
    history_entry = EntryDto(**response_data)
    assert history_entry.version == 2


class TestGetEntryDiff:
    def test_diff1(
        self,
        fa_data_client,
        user4_token: auth.AccessToken,
        history_entity_ids: list[str],
    ):
        response = fa_data_client.post(
            f"/history/diff/places/{history_entity_ids[0]}?from_version=1&to_version=2",
            headers=user4_token.as_header(),
        )
        response_data = response.json()
        print(f"response_data = {response_data}")
        assert response.status_code == status.HTTP_200_OK

        diff = response_data["diff"]
        assert len(diff) == 1
        assert "CHANGE" == diff[0]["type"]
        assert "a" == diff[0]["before"]
        assert "aa" == diff[0]["after"]
        assert "name" == diff[0]["field"]
        assert response_data["from_version"] == 1
        assert response_data["to_version"] == 2

    def test_diff2(
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
        response_data = response.json()
        diff = response_data["diff"]
        print(f"response = {response_data}")
        assert "a" == diff[0]["before"]
        assert "aaaaaaaaa" == diff[0]["after"]
        assert response_data["from_version"] == 1
        assert response_data["to_version"] == 9

    def test_diff_from_first_to_date(
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
        response_data = response.json()
        diff = response_data["diff"]
        assert "a" == diff[0]["before"]
        assert diff[0]["after"] > "aaaaaa"
        assert response_data["from_version"] == 1
        assert response_data["to_version"] > 6

    @pytest.mark.xfail()
    def test_diff_from_date_to_last(
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
        response_data = response.json()
        diff = response_data["diff"]
        assert "aaaaaaaa" == diff[0]["before"]
        assert "aaaaaaaaa" == diff[0]["after"]
        assert response_data["from_version"] == 8
        assert response_data["to_version"] == 9

    def test_diff_from_first_to_version(
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
        response_data = response.json()
        diff = response_data["diff"]
        assert "a" == diff[0]["before"]
        assert "aaaaaaa" == diff[0]["after"]
        assert response_data["from_version"] == 1
        assert response_data["to_version"] == 7

    def test_diff_from_version_to_last(
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
        response_data = response.json()
        diff = response_data["diff"]
        assert "aaaaaaa" == diff[0]["before"]
        assert "aaaaaaaaa" == diff[0]["after"]
        assert response_data["from_version"] == 7
        assert response_data["to_version"] == 9

    def test_diff_mix_version_date(
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
        response_data = response.json()
        diff = response_data["diff"]
        assert "aa" == diff[0]["before"]
        assert diff[0]["after"] > "aaaaaa"
        assert response_data["from_version"] == 2
        assert response_data["to_version"] > 6

    def test_diff_to_entry_data(
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
        response_data = response.json()
        diff = response_data["diff"]
        assert "a" == diff[0]["before"]
        assert "testing" == diff[0]["after"]
        assert response_data["from_version"] == 1
        assert response_data["to_version"] is None

    def test_diff_no_flags(
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
        response_data = response.json()
        diff = response_data["diff"]
        assert "a" == diff[0]["before"]
        assert "aaaaaaaaa" == diff[0]["after"]
        assert response_data["from_version"] == 1
        assert response_data["to_version"] == 9
