from karp.domain.services.network import _create_ref


def test__create_ref():
    resource_id = "resource_id"
    resource_version = 1
    _id = 5
    entry_id = "entry_id"
    entry_body = {"body": {"of": "entry"}}

    ref = _create_ref(resource_id, resource_version, _id, entry_id, entry_body)

    assert ref["resource_id"] == resource_id
    assert ref["resource_version"] == resource_version
    assert ref["id"] == _id
    assert ref["entry_id"] == entry_id
    assert ref["entry"] == entry_body
