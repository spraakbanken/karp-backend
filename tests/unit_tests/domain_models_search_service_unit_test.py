from karp.domain.models.search_service import IndexEntry, SearchService


def test_create_empty_object_returns_index_entry():
    search = SearchService()

    index_entry = search.create_empty_object()

    assert isinstance(index_entry, IndexEntry)
    assert index_entry.id == ""
    assert index_entry.entry == {}
