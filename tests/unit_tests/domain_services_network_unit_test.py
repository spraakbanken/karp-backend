from karp.domain.services.network import _create_ref
from karp.domain.models.entry import create_entry


def test__create_ref():
    resource_id = "resource_id"
    resource_version = 1
    _id = 5
    entry_id = "entry_id"
    entry_body = {"body": {"of": "entry"}}
    entry = create_entry(entry_id, entry_body)

    ref = _create_ref(resource_id, resource_version, entry)

    assert ref["resource_id"] == resource_id
    assert ref["resource_version"] == resource_version
    # assert ref["entry"]["id"] == _id
    assert ref["entry"].entry_id == entry_id
    assert ref["entry"].body == entry_body
