import pytest

from karp import search


@pytest.fixture
def query():
    return search.Query()


def test_empty_arg_and_empty_resource_str(query):
    with pytest.raises(search.errors.IncompleteQuery):
        query.parse_arguments({}, None)


def test_minimal(query):
    query.parse_arguments({}, 'saldo')
    assert isinstance(query.resources, list)
    assert len(query.resources) == 1
    assert query.resources[0] == 'saldo'
