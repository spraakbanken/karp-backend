from karp.domain.services.network import get_refs

from karp.application import ctx


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


def test_no_refs_1(app_with_data_f):
    app = app_with_data_f()

    with app.app_context():
        entrywrite.add_entries("places", places[0:1], "test", resource_version=1)

        referenced_entries = list(network.get_referenced_entries("places", 1, "3"))
        assert len(referenced_entries) == 0


def test_no_refs_2(app_with_data_f):
    app = app_with_data_f()

    with app.app_context():
        entrywrite.add_entries("places", places[0:2], "test", resource_version=1)

        referenced_entries = list(network.get_referenced_entries("places", 1, "3"))
        assert len(referenced_entries) == 0
        referenced_entries = list(network.get_referenced_entries("places", 1, "4"))
        assert len(referenced_entries) == 0


def test_internal_ref(app_with_data_f):
    app = app_with_data_f()

    with app.app_context():
        entrywrite.add_entries("places", places[1:3], "test", resource_version=1)

        referenced_entries = list(network.get_referenced_entries("places", 1, "5"))
        assert len(referenced_entries) == 1
        assert referenced_entries[0]["entry_id"] == "4"


def test_external_ref(app_with_data_f):
    app = app_with_data_f()

    with app.app_context():
        entrywrite.add_entries("places", places, "test", resource_version=1)
        entrywrite.add_entries(
            "municipalities", municipalities, "test", resource_version=1
        )

        referenced_entries = list(network.get_referenced_entries("places", 1, "3"))
        assert len(referenced_entries) == 1
        assert referenced_entries[0]["entry_id"] == "1"

        referenced_entries = list(network.get_referenced_entries("places", 1, "4"))
        assert 3 == len(referenced_entries)
        ref_municipalities = [
            entry
            for entry in referenced_entries
            if entry["resource_id"] == "municipalities"
        ]
        assert ref_municipalities[0]["entry_id"] in ["2", "3"]
        assert ref_municipalities[1]["entry_id"] in ["2", "3"]
        assert ref_municipalities[0]["entry_id"] != ref_municipalities[1]["id"]

        referenced_entries = list(network.get_referenced_entries("places", 1, "5"))
        assert len(referenced_entries) == 3
        ref_municipalities = [
            entry
            for entry in referenced_entries
            if entry["resource_id"] == "municipalities"
        ]
        assert ref_municipalities[0]["entry_id"] in ["2", "3"]
        assert ref_municipalities[1]["entry_id"] in ["2", "3"]
        assert ref_municipalities[0]["entry_id"] != ref_municipalities[1]["id"]


def test_virtual_internal_ref(app_with_data_f):
    app = app_with_data_f()

    with app.app_context():
        entrywrite.add_entries("places", places[1:3], "test", resource_version=1)

        referenced_entries = list(network.get_referenced_entries("places", 1, "4"))
        assert 1 == len(referenced_entries)
        assert referenced_entries[0]["entry_id"] == "5"


def test_virtual_external_ref(app_with_data_f):
    app = app_with_data_f()

    with app.app_context():
        entrywrite.add_entries("places", places[0:1], "test", resource_version=1)
        entrywrite.add_entries(
            "municipalities", municipalities[0:1], "test", resource_version=1
        )

        referenced_entries = list(
            network.get_referenced_entries("municipalities", 1, "1")
        )
        assert 1 == len(referenced_entries)
        assert referenced_entries[0]["resource_id"] == "places"
        assert referenced_entries[0]["entry_id"] == "3"
