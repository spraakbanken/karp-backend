from typing import List

import pytest

from karp.search.application.queries import QueryRequest
from karp.search.domain.query import Query
from karp.search_infrastructure.queries import EsQuery


@pytest.fixture()
def resource_ids() -> List[str]:
    return ["resource_a"]


@pytest.fixture()
def request_from() -> int:
    return 4


@pytest.fixture()
def request_size() -> int:
    return 5


@pytest.fixture()
def query_request(
    resource_ids: List[str], request_from: int, request_size: int
) -> QueryRequest:
    return QueryRequest(
        resource_ids=resource_ids, from_=request_from, size=request_size
    )


def test_create_EsQuery_from_QueryRequest(query_request: QueryRequest) -> None:
    query = EsQuery.from_query_request(query_request)

    assert query.from_ == query_request.from_
    assert query.size == query_request.size
