from karp.domain.services.indexing import transform_to_index_entry

from karp.application import ctx


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

    assert isinstance(index_entry, dict)
    print(f"index_entry = {index_entry}")
    assert "v_municipality" in index_entry
