from karp.application import ctx
from karp.application.services import entries
from karp.domain.services.network import get_referenced_entries, get_refs


def test_get_refs_for_places(
    places_published_scope_module, municipalities_published_scope_module
):
    resource_id = "places"
    refs, backrefs = get_refs(ctx.resource_repo, resource_id)

    assert len(refs) == 2

    assert refs[0][0:3] == ("municipalities", 1, "municipality")
    assert refs[1][0:3] == ("places", None, "larger_place")

    assert len(backrefs) == 1

    assert backrefs[0][0:3] == ("places", None, "larger_place")


def test_get_refs_for_municipalities(
    places_published_scope_module, municipalities_published_scope_module
):
    resource_id = "municipalities"
    refs, backrefs = get_refs(ctx.resource_repo, resource_id)

    assert len(refs) == 0

    # assert refs[0][0:3] == ("municipalities", 1, "municipality")
    # assert refs[1][0:3] == ("places", None, "larger_place")

    assert len(backrefs) == 1

    assert backrefs[0][0:3] == ("places", 1, "municipality")


places = [
    {"code": 3, "name": "a", "municipality": [1]},
    {"code": 4, "name": "b", "municipality": [2, 3]},
    {"code": 5, "name": "c", "municipality": [2, 3], "larger_place": 4},
]

municipalities = [
    {"name": "d", "code": 1},
    {"name": "e", "code": 2},
    {"name": "f", "code": 3},
]


def test_no_refs_1(
    places_published_scope_module, municipalities_published_scope_module
):
    entries.add_entries("places", places[0:1], "test", resource_version=1)

    referenced_entries = list(
        get_referenced_entries(ctx.resource_repo, places_published_scope_module, 1, "3")
    )
    assert len(referenced_entries) == 0


def test_no_refs_2(
    places_published_scope_module, municipalities_published_scope_module
):
    entries.add_entries("places", places[1:2], "test", resource_version=1)

    referenced_entries = list(
        get_referenced_entries(ctx.resource_repo, places_published_scope_module, 1, "3")
    )
    assert len(referenced_entries) == 0
    referenced_entries = list(
        get_referenced_entries(ctx.resource_repo, places_published_scope_module, 1, "4")
    )
    assert len(referenced_entries) == 0


def test_internal_ref(
    places_published_scope_module, municipalities_published_scope_module
):
    entries.add_entries("places", places[2:3], "test", resource_version=1)

    referenced_entries = list(
        get_referenced_entries(ctx.resource_repo, places_published_scope_module, 1, "5")
    )
    assert len(referenced_entries) == 1
    assert referenced_entries[0]["entry"].entry_id == "4"


def test_external_ref(
    places_published_scope_module, municipalities_published_scope_module
):
    # entries.add_entries("places", places, "test", resource_version=1)
    entries.add_entries("municipalities", municipalities, "test", resource_version=1)

    referenced_entries = list(
        get_referenced_entries(ctx.resource_repo, places_published_scope_module, 1, "3")
    )
    assert len(referenced_entries) == 1
    assert referenced_entries[0]["entry"].entry_id == "1"

    referenced_entries = list(
        get_referenced_entries(ctx.resource_repo, places_published_scope_module, 1, "4")
    )
    assert 3 == len(referenced_entries)
    ref_municipalities = [
        entry
        for entry in referenced_entries
        if entry["resource_id"] == "municipalities"
    ]
    assert ref_municipalities[0]["entry"].entry_id in ["2", "3"]
    assert ref_municipalities[1]["entry"].entry_id in ["2", "3"]
    assert (
        ref_municipalities[0]["entry"].entry_id
        != ref_municipalities[1]["entry"].entry_id
    )
    assert ref_municipalities[0]["entry"].entry_id != ref_municipalities[1]["entry"].id

    referenced_entries = list(
        get_referenced_entries(ctx.resource_repo, places_published_scope_module, 1, "5")
    )
    assert len(referenced_entries) == 3
    ref_municipalities = [
        entry
        for entry in referenced_entries
        if entry["resource_id"] == "municipalities"
    ]
    assert ref_municipalities[0]["entry"].entry_id in ["2", "3"]
    assert ref_municipalities[1]["entry"].entry_id in ["2", "3"]
    assert (
        ref_municipalities[0]["entry"].entry_id
        != ref_municipalities[1]["entry"].entry_id
    )


def test_virtual_internal_ref(
    places_published_scope_module, municipalities_published_scope_module
):

    # entries.add_entries("places", places[1:3], "test", resource_version=1)

    referenced_entries = list(
        get_referenced_entries(ctx.resource_repo, places_published_scope_module, 1, "4")
    )
    assert len(referenced_entries) == 3
    assert referenced_entries[0]["resource_id"] == "places"
    assert referenced_entries[0]["entry"].entry_id == "5"

    assert referenced_entries[1]["resource_id"] == "municipalities"
    assert referenced_entries[1]["entry"].entry_id == "2"

    assert referenced_entries[2]["resource_id"] == "municipalities"
    assert referenced_entries[2]["entry"].entry_id == "3"


def test_virtual_external_ref(
    places_published_scope_module, municipalities_published_scope_module
):
    # entries.add_entries("places", places[0:1], "test", resource_version=1)
    # entries.add_entries(
    #     "municipalities", municipalities[0:1], "test", resource_version=1
    # )

    referenced_entries = list(
        get_referenced_entries(
            ctx.resource_repo, municipalities_published_scope_module, 1, "1"
        )
    )
    assert len(referenced_entries) == 2
    assert referenced_entries[0]["resource_id"] == "places"
    assert referenced_entries[0]["entry"].entry_id == "3"

    assert referenced_entries[1]["resource_id"] == "places"
    assert referenced_entries[1]["entry"].entry_id == "3"
