# import pytest  # pyre-ignore

from karp import resourcemgr


def test_field_mappings_empty(client_with_entries_scope_session):
    assert isinstance(resourcemgr.field_translations, dict)

    r = resourcemgr.get_field_translations('places')
    assert r == {'state': ['v_municipality.state']}
