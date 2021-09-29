from karp.application import ctx
from karp.domain.models.search_service import IndexEntry
from karp.domain.services.indexing import (_transform_to_index_entry,
                                           transform_to_index_entry)


def test_transform_to_index_entry(
    places_published_scope_module, municipalities_published_scope_module
):
    src_entry = places_published_scope_module.create_entry_from_dict(
        {
            "code": 11,
            "name": "Grund test1",
            "population": 31221,
            "area": 63121,
            "density": 63112,
            "municipality": [1],
            "larger_place": 7  # Alhamn
            # "smaller_places": 9 "Bjurvik2"
        },
        user="TestUser",
    )
    index_entry = transform_to_index_entry(
        ctx.resource_repo, ctx.search_service, places_published_scope_module, src_entry
    )

    assert isinstance(index_entry, IndexEntry)
    assert index_entry.id == src_entry.entry_id
    print(f"index_entry = {index_entry}")
    assert "v_municipality" in index_entry.entry


def test__transform_to_index_entry_1(
    places_published_scope_module, municipalities_published_scope_module
):
    src_entry = places_published_scope_module.create_entry_from_dict(
        {
            "code": 11,
            "name": "Grund test1",
            "population": 31221,
            "area": 63121,
            "density": 63112,
            "municipality": [1],
            "larger_place": 7  # Alhamn
            # "smaller_places": 9 "Bjurvik2"
        },
        user="TestUser",
    )
    index_entry = ctx.search_service.create_empty_object()
    _transform_to_index_entry(
        places_published_scope_module,
        ctx.resource_repo,
        ctx.search_service,
        src_entry.body,
        index_entry,
        places_published_scope_module.config["fields"].items(),
    )

    assert isinstance(index_entry, IndexEntry)
    print(f"index_entry = {index_entry}")
    assert "v_municipality" in index_entry.entry
    assert "smaller_places" not in index_entry.entry
    assert "v_smaller_places" not in index_entry.entry
    # assert not isinstance(index_entry.entry["smaller_places"], IndexEntry)
