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
