import json
import pytest  # pyre-ignore
from datetime import datetime, timezone
import time

places = [
    {"code": 3, "name": "a", "municipality": [1]},
    {"code": 4, "name": "b", "municipality": [2, 3]},
    {"code": 5, "name": "c", "municipality": [2, 3], "larger_place": 4},
]


@pytest.fixture(scope="module", name="fa_diff_data_client")
def fixture_fa_diff_data_client(fa_client_w_places_scope_module):
    response = fa_client_w_places_scope_module.post(
        "places/add",
        json={"entry": places[0]},
        headers={"Authorization": "Bearer 1234"},
    )
    assert response.status_code == 201
    new_id = response.json()["newID"]
    time.sleep(1)
    for i in range(2, 10):
        changed_entry = places[0].copy()
        changed_entry["name"] = places[0]["name"] * i
        response = fa_client_w_places_scope_module.post(
            f"places/{new_id}/update",
            json={"entry": changed_entry, "message": "changes", "version": i - 1},
            headers={"Authorization": "Bearer 1234"},
        )
        print(f"response = {response.json()}")
        assert response.status_code == 200
        time.sleep(1)

    return fa_client_w_places_scope_module
