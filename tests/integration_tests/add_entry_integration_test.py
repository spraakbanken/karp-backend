import json
from karp.resourcemgr.entrywrite import add_entry

from tests.utils import get_json


def test_config_with_field_both_object_and_collection(
    client_with_entries_scope_session,
):
    entry = {
        "lemgram": "väffse..e.1",
        "etymology": [
            {"language": "dan", "form": "hveps"},
            {"language": "deu", "form": "wespe"},
        ],
    }
    resource = "alphalex"
    resp = client_with_entries_scope_session.post(
        f"/{resource}/add",
        data=json.dumps({"entry": entry}),
        content_type="application/json",
    )
    assert resp.status_code < 300, resp
