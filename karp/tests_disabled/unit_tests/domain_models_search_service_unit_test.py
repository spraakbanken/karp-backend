from re import search

from karp.domain.models.search_service import IndexEntry, SearchService


def test_create_empty_object_returns_index_entry():
    search = SearchService()

    index_entry = search.create_empty_object()

    assert isinstance(index_entry, IndexEntry)
    assert index_entry.id == ""
    assert index_entry.entry == {}


def test_assign_field_adds_field_to_index_entry():
    search = SearchService()

    index_entry = search.create_empty_object()

    search.assign_field(index_entry, "field", {})
    assert index_entry.entry["field"] == {}


def test_create_empty_list_returns_list():
    search = SearchService()

    index_list = search.create_empty_list()

    assert isinstance(index_list, list)
    assert index_list == []


def test_add_to_list_field_adds_to_list():
    search = SearchService()

    index_list = search.create_empty_list()

    search.add_to_list_field(index_list, "a")

    assert index_list == ["a"]

    search.add_to_list_field(index_list, {"b": "c"})

    assert index_list == ["a", {"b": "c"}]


def test_empty_index_entry_evaluates_to_false():
    index_entry = IndexEntry()

    assert not index_entry
