from karp.application.services import resources


def test_field_mappings_empty(places_published):

    r = resources.get_field_translations("places")
    assert r == {"state": ["v_municipality.state"]}
