from karp.lex_infrastructure.queries import generic_network  # noqa: I001

from karp.tests.unit.lex import factories


def test__create_ref():  # noqa: ANN201
    resource_id = "resource_id"
    resource_version = 1
    _id = 5
    entry_body = {"body": {"of": "entry"}}
    entry = factories.EntryFactory(body=entry_body)

    ref = generic_network._create_ref(resource_id, resource_version, entry)

    assert ref.resource_id == resource_id
    assert ref.resource_version == resource_version
    # assert ref["entry"]["id"] == _id
    assert ref.entry.id == entry.id
    assert ref.entry.entry == entry_body
