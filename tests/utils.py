"""Handle calls and json convertions."""
import json
from typing import Dict


def get_json(client, path: str):
    """Call the get on the client with the given path.

    Assert that the status_code is ok.
    Then load the json response.

    Arguments:
        client {[type]} -- [description]
        path {[type]} -- [description]

    Returns:
        [type] -- [description]
    """
    response = client.get(path)
    assert 200 <= response.status_code < 300
    return response.json()


def add_entries(client, entries: Dict):
    for resource, _entries in entries.items():
        for entry in _entries:
            response = client.post(
                f"{resource}/add",
                json={"entry": entry},
                headers={"Authorization": "Bearer 1234"},
            )
            assert response.status_code == 201
    return client
