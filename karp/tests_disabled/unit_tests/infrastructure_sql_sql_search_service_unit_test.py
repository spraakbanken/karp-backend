from unittest import mock

from karp.domain.models.search_service import IndexEntry
from karp.infrastructure.sql.sql_search_service import SqlSearchService


def test_create_empty_object_returns_index_entry():
    sql_search = SqlSearchService()

    index_entry = sql_search.create_empty_object()

    assert isinstance(index_entry, IndexEntry)
