from karp.domain import model, events

from karp.tests import common_data
from karp.utility import unique_id


def random_entry():
    return model.Entry(
        entity_id=unique_id.make_unique_id(),
        entry_id="a",
        body={},
        resource_id="b",
        message="add",
        last_modified_by="kristoff@example.com",
        last_modified=12345.67,
    )


def test_new_entry_has_event():
    entry = random_entry()
    assert entry.events[-1] == events.EntryAdded(
        id=entry.id,
        entry_id=entry.entry_id,
        resource_id=entry.resource_id,
        body=entry.body,
        user=entry.last_modified_by,
        timestamp=entry.last_modified,
        message=entry.message,
    )


def test_discarded_entry_has_event():
    entry = random_entry()
    entry.discard(
        user="alice@example.org",
        message="bad",
        timestamp=123.45
    )
    assert entry.discarded
    assert entry.events[-1] == events.EntryDiscarded(
        id=entry.id,
        entry_id=entry.entry_id,
        resource_id=entry.resource_id,
        user=entry.last_modified_by,
        timestamp=entry.last_modified,
        message=entry.message,
        version=2,
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
