from karp.domain import model, events

from karp.tests import common_data
from karp.utility import unique_id


def test_new_entry_has_event():
    entity_id = unique_id.make_unique_id(),
    entry = model.Entry(
        entity_id=entity_id,
        entry_id="a",
        body={},
        resource_id="b",
        message="add",
        last_modified_by="kristoff@example.com",
        last_modified=12345.67,
    )
    assert entry.events[-1] == events.EntryAdded(
        id=entity_id,
        entry_id="a",
        resource_id="b",
        body={},
        user="kristoff@example.com",
        timestamp=12345.67,
        message="add"
    )


# def test_resource_create_entry_from_raw():
#     resource = create_resource(
#         {
#             "resource_id": "places",
#             "resource_name": "Platser i Sverige",
#             "fields": {
#                 "name": {"type": "string", "required": True},
#                 "municipality": {
#                     "collection": True,
#                     "type": "number",
#                     "required": True,
#                 },
#                 "population": {"type": "number"},
#                 "area": {"type": "number"},
#                 "density": {"type": "number"},
#                 "code": {"type": "number", "required": True},
#             },
#             "sort": "name",
#             "id": "code",
#         }
#     )
#
#     entry = entry_lifecycle.create_entry_from_dict(resource, common_data.PLACES[0])
#
#     assert isinstance(entry, Entry)
#     assert entry.entry_id == "1"
