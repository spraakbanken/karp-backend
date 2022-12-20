"""Handle calls and json convertions."""
import json
from typing import Dict
from fastapi import status
from karp import auth


def get_json(
    client, path: str, expected_status_code: int = status.HTTP_200_OK, **kwargs
):
    """Call the get on the client with the given path.

    Assert that the status_code is ok.
    Then load the json response.

    Arguments:
        client {[type]} -- [description]
        path {[type]} -- [description]

    Returns:
        [type] -- [description]
    """
    response = client.get(path, **kwargs)
    response_json = response.json()
    print(f"{response_json=}")
    assert response.status_code == expected_status_code
    return response_json


def add_entries(
    client,
    entries: Dict,
    access_token: auth.AccessToken,
):
    for resource, _entries in entries.items():
        for entry in _entries:
            response = client.post(
                f"/entries/{resource}/add",
                json={"entry": entry},
                headers=access_token.as_header(),
            )
            assert (
                response.status_code == 201
            ), f"Response(status_code={response.status_code}, json={response.json()})"
    return client
