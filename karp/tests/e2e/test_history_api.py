# import json
import re
import time
from datetime import datetime, timezone

import pytest  # pyre-ignore

# import karp.resourcemgr.entrywrite as entrywrite
# from karp.application.services import entries
from karp.utility.time import utc_now

places = [
    {"code": 103, "name": "a", "municipality": [1]},
    {"code": 104, "name": "b", "municipality": [2, 3]},
    {"code": 105, "name": "c", "municipality": [2, 3], "larger_place": 4},
    {"code": 106, "name": "c", "municipality": [1], "larger_place": 5},
]


def get_helper(client, url):
    response = client.get(
        url,
        headers={"Authorization": "Bearer 1234"},
    )
    assert response.status_code == 200
    return response.json()


def username(name: str) -> str:
    return f"{__name__}-{name}"


@pytest.fixture(name="fa_history_data_client", scope="session")
def fixture_fa_history_data_client(fa_client, main_db, places_published):
    for entry in places[0:2]:
        response = fa_client.post(
            "/places/add",
            json={"entry": entry, "message": "Add it"},
            headers={"Authorization": "Bearer user1"},
        )
        print(f'{response.json()=}')
        assert response.status_code == 201
        # entries.add_entry("places", entry, "user1", message="Add it")
        time.sleep(1)
    for entry in places[2:]:
        fa_client.post(
            "/places/add",
            json={"entry": entry, "message": "Add it"},
            headers={"Authorization": "Bearer user2"},
        )
        # entries.add_entry("places", entry, "user2", message="Add it")
        time.sleep(1)
    for entry in places[0:2]:
        changed_entry = entry.copy()
        changed_entry["name"] = entry["name"] + entry["name"]
        fa_client.post(
            f"/places/{entry['code']}/update",
            json={"entry": changed_entry, "message": "change it", "version": 1},
            headers={"Authorization": "Bearer user2"},
        )
        # entries.update_entry(
        #     "places",
        #     str(entry["code"]),
        #     1,
        #     changed_entry,
        #     "user2",
        #     message="Change it",
        # )
        time.sleep(1)
    for entry in places[2:]:
        changed_entry = entry.copy()
        changed_entry["name"] = entry["name"] + entry["name"]
        fa_client.post(
            f"/places/{entry['code']}/update",
            json={"entry": changed_entry, "message": "change it", "version": 1},
            headers={"Authorization": "Bearer user1"},
        )
        # entries.update_entry(
        #     "places",
        #     str(entry["code"]),
        #     1,
        #     changed_entry,
        #     "user1",
        #     message="Change it",
        # )
        time.sleep(1)

    diff_entry_id = places[0]["code"]
    for i in range(3, 10):
        changed_entry = places[0].copy()
        changed_entry["name"] = places[0]["name"] * i
        response = fa_client.post(
            f"places/{diff_entry_id}/update",
            json={"entry": changed_entry,
                  "message": "changes", "version": i - 1},
            headers={"Authorization": "Bearer user4"},
        )
        print(f"response = {response.json()}")
        assert response.status_code == 200
        time.sleep(1)
    return fa_client


def test_empty_user_history(fa_history_data_client):
    response_data = get_helper(
        fa_history_data_client, "/places/history?user_id=user3")
    assert len(response_data["history"]) == 0
    assert response_data["total"] == 0


def test_user1_history(fa_history_data_client):
    response_data = get_helper(
        fa_history_data_client, "places/history?user_id=user1")
    assert len(response_data["history"]) == 4
    assert response_data["total"] == 4
    for history_entry in response_data["history"]:
        assert "user1" == history_entry["user_id"]


def test_user2_history(fa_history_data_client):
    response_data = get_helper(
        fa_history_data_client, "places/history?user_id=user2")
    assert 4 == len(response_data["history"])
    assert response_data["history"][0]["op"] == "ADDED"
    assert response_data["history"][1]["op"] == "ADDED"
    assert "UPDATED" == response_data["history"][2]["op"]
    assert "UPDATED" == response_data["history"][3]["op"]
    assert re.match(r"^\d{10}\.\d{3,6}$", str(
        response_data["history"][3]["timestamp"]))
    for history_entry in response_data["history"]:
        assert "user2" == history_entry["user_id"]


def test_user_history_from_date(fa_history_data_client):
    response_data = get_helper(
        fa_history_data_client,
        f"places/history?user_id=user1&from_date={utc_now() - 5}",
    )
    assert 4 > len(response_data["history"]), len(response_data["history"])


def test_user_history_to_date(fa_history_data_client):
    response_data = get_helper(
        fa_history_data_client,
        f"/places/history?user_id=user2&to_date={utc_now() - 5}",
    )
    assert len(response_data["history"]) == 4


def test_entry_id(fa_history_data_client):
    response_data = get_helper(
        fa_history_data_client, "places/history?entry_id=104")
    assert 2 == len(response_data["history"])
    for history_entry in response_data["history"]:
        assert "104" == history_entry["entry_id"]


def test_entry_id_and_user_id(fa_history_data_client):
    response_data = get_helper(
        fa_history_data_client, "places/history?entry_id=103&user_id=user2"
    )
    assert 1 == len(response_data["history"])
    history_entry = response_data["history"][0]
    assert "103" == history_entry["entry_id"]
    assert "user2" == history_entry["user_id"]
    assert "UPDATED" == history_entry["op"]


def test_diff_against_nothing(fa_history_data_client):
    response_data = get_helper(
        fa_history_data_client, "places/history?entry_id=103&to_version=2"
    )
    assert 1 == len(response_data["history"])
    history_entry = response_data["history"][0]
    assert "ADDED" == history_entry["op"]
    for diff in history_entry["diff"]:
        print(f"diff = {diff}")
        assert "ADDED" == diff["type"]


def test_historical_entry(fa_history_data_client):
    response_data = get_helper(fa_history_data_client, "places/104/2/history")
    print(f"got data")
    assert utc_now() > response_data["last_modified"]
    assert "user2" == response_data["last_modified_by"]
    assert "entry_id" in response_data
    assert "resource" in response_data
    assert "bb" == response_data["entry"]["name"]
    assert "version" in response_data


def test_diff1(fa_history_data_client):
    response = fa_history_data_client.get(
        "places/103/diff?from_version=1&to_version=2",
        headers={"Authorization": "Bearer user4"},
    )
    response_data = response.json()
    print(f"response_data = {response_data}")
    diff = response_data["diff"]
    assert len(diff) == 1
    assert "CHANGE" == diff[0]["type"]
    assert "a" == diff[0]["before"]
    assert "aa" == diff[0]["after"]
    assert "name" == diff[0]["field"]
    assert response_data["from_version"] == 1
    assert response_data["to_version"] == 2


def test_diff2(fa_history_data_client):
    response = fa_history_data_client.get(
        f"/places/103/diff?from_date=0&to_date={utc_now()}",
        headers={"Authorization": "Bearer user4"},
    )
    response_data = response.json()
    diff = response_data["diff"]
    print(f"response = {response_data}")
    assert "a" == diff[0]["before"]
    assert "aaaaaaaaa" == diff[0]["after"]
    assert response_data["from_version"] == 1
    assert response_data["to_version"] == 9


def test_diff_from_first_to_date(fa_history_data_client):
    """
    this test is a bit shaky due to assuming that we will find the correct version by subtracting three seconds
    """
    response = fa_history_data_client.get(
        f"/places/103/diff?to_date={utc_now() - 3}",
        headers={"Authorization": "Bearer user4"},
    )
    response_data = response.json()
    diff = response_data["diff"]
    assert "a" == diff[0]["before"]
    assert "aaaaaaa" == diff[0]["after"]
    assert response_data["from_version"] == 1
    assert response_data["to_version"] == 7


def test_diff_from_date_to_last(fa_history_data_client):
    """
    this test is a bit shaky due to assuming that we will find the correct version by subtracting three seconds
    """
    response = fa_history_data_client.get(
        f"/places/103/diff?from_date={utc_now() - 3}",
        headers={"Authorization": "Bearer user4"},
    )
    response_data = response.json()
    diff = response_data["diff"]
    assert "aaaaaaaa" == diff[0]["before"]
    assert "aaaaaaaaa" == diff[0]["after"]
    assert response_data["from_version"] == 8
    assert response_data["to_version"] == 9


def test_diff_from_first_to_version(fa_history_data_client):
    response = fa_history_data_client.get(
        "places/103/diff?to_version=7",
        headers={"Authorization": "Bearer user4"},
    )
    response_data = response.json()
    diff = response_data["diff"]
    assert "a" == diff[0]["before"]
    assert "aaaaaaa" == diff[0]["after"]
    assert response_data["from_version"] == 1
    assert response_data["to_version"] == 7


def test_diff_from_version_to_last(fa_history_data_client):
    response = fa_history_data_client.get(
        "places/103/diff?from_version=7",
        headers={"Authorization": "Bearer user4"},
    )
    response_data = response.json()
    diff = response_data["diff"]
    assert "aaaaaaa" == diff[0]["before"]
    assert "aaaaaaaaa" == diff[0]["after"]
    assert response_data["from_version"] == 7
    assert response_data["to_version"] == 9


def test_diff_mix_version_date(fa_history_data_client):
    response = fa_history_data_client.get(
        f"/places/103/diff?from_version=2&to_date={utc_now() - 3}",
        headers={"Authorization": "Bearer user4"},
    )
    response_data = response.json()
    diff = response_data["diff"]
    assert "aa" == diff[0]["before"]
    assert "aaaaaaa" == diff[0]["after"]
    assert response_data["from_version"] == 2
    assert response_data["to_version"] == 7


def test_diff_to_entry_data(fa_history_data_client):
    edited_entry = places[0].copy()
    edited_entry["name"] = "testing"
    response = fa_history_data_client.get(
        "places/103/diff?from_version=1",
        json=edited_entry,
        headers={"Authorization": "Bearer user4"},
    )
    response_data = response.json()
    diff = response_data["diff"]
    assert "a" == diff[0]["before"]
    assert "testing" == diff[0]["after"]
    assert response_data["from_version"] == 1
    assert response_data["to_version"] is None


def test_diff_no_flags(fa_history_data_client):
    response = fa_history_data_client.get(
        "places/103/diff?from_version=1",
        headers={"Authorization": "Bearer user4"},
    )
    response_data = response.json()
    diff = response_data["diff"]
    assert "a" == diff[0]["before"]
    assert "aaaaaaaaa" == diff[0]["after"]
    assert response_data["from_version"] == 1
    assert response_data["to_version"] == 9
