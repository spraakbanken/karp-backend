import pytest  # pyre-ignore

from karp.domain import errors
from karp.domain.models.query import (
    # create_query,
    Query,
    #    StatsQuery,
)


@pytest.fixture
def query():
    return Query()


def test_empty_arg_and_empty_resource_str(query):
    with pytest.raises(errors.IncompleteQuery):
        query.parse_arguments({}, None)


def test_minimal(query):
    query.parse_arguments({"sort": "quiet"}, "saldo")
    assert isinstance(query.resources, list)
    assert len(query.resources) == 1
    assert query.resources[0] == "saldo"


# def test_create_query_creates_query():
#     resource_str = "test"
#     # query = create_query(resource_str)
#     query = Query()
#
#     assert isinstance(query, Query)
#     # assert isinstance(query, StatsQuery)
#
#     assert len(query.resources) == 1
#     assert query.resources[0] == resource_str
