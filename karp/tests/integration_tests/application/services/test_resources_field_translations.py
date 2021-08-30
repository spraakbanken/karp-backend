from karp.services import resource_handlers


def test_field_mappings_empty(places_published):

    r = resource_handlers.get_field_translations("places")
    assert r == {"state": ["v_municipality.state"]}
