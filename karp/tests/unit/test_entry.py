from karp.domain.models.resource import create_resource
from karp.domain.models.entry import Entry
from karp.domain.services import entry_lifecycle

from karp.tests import common_data


def test_resource_create_entry_from_raw():
    resource = create_resource(
        {
            "resource_id": "places",
            "resource_name": "Platser i Sverige",
            "fields": {
                "name": {"type": "string", "required": True},
                "municipality": {
                    "collection": True,
                    "type": "number",
                    "required": True,
                },
                "population": {"type": "number"},
                "area": {"type": "number"},
                "density": {"type": "number"},
                "code": {"type": "number", "required": True},
            },
            "sort": "name",
            "id": "code",
        }
    )

    entry = entry_lifecycle.create_entry_from_dict(resource, common_data.PLACES[0])

    assert isinstance(entry, Entry)
    assert entry.entry_id == "1"
