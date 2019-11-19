"""Handle calls and json convertions."""
import json


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
    return json.loads(response.data.decode())
