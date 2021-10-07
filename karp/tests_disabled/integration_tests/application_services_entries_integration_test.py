from karp.application.services.entries import add_entries
from karp.tests import common_data


def test_add_municipality(
    places_published_scope_module, municipalities_published_scope_module
):
    resource_id = "municipalities"
    user_id = "TestUser"

    entries = add_entries(resource_id, common_data.MUNICIPALITIES, user_id)

    assert len(entries) == 3
    assert entries[0].entry_id == "1"
