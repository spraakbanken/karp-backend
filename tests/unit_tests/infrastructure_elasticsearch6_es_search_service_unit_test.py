from unittest import mock


from karp.domain.models.search_service import IndexEntry
from karp.infrastructure.elasticsearch6.es6_search_service import Es6SearchService


def test_create_empty_object_returns_index_entry():
    es_mock = mock.Mock()
    es_mock.cat.aliases.return_value = ".one\n"
    es6_search = Es6SearchService(es_mock)

    index_entry = es6_search.create_empty_object()

    assert isinstance(index_entry, IndexEntry)
