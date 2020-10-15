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
