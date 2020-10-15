from unittest import mock

import pytest

from karp.domain.models.search_service import IndexEntry
from karp.infrastructure.elasticsearch6.es6_search_service import Es6SearchService


@pytest.fixture(name="es6_search")
def fixture_es6_search():
    es_mock = mock.Mock()
    es_mock.cat.aliases.return_value = ".one\n"
    return Es6SearchService(es_mock)


def test_create_empty_object_returns_index_entry(es6_search):

    index_entry = es6_search.create_empty_object()

    assert isinstance(index_entry, IndexEntry)
    assert index_entry.id == ""
    assert index_entry.entry == {}


def test_assign_field_adds_field_to_index_entry(es6_search):

    index_entry = es6_search.create_empty_object()

    es6_search.assign_field(index_entry, "field", {})
    assert index_entry.entry["field"] == {}
