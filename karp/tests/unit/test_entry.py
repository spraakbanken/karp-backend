from typing import Dict
import pytest

from karp.domain import model, events, errors

from karp.tests import common_data
from karp.utility import unique_id


def random_entry(entry_id: str = None, body: Dict = None):
    return model.create_entry(
        entity_id=unique_id.make_unique_id(),
        entry_id=entry_id or "a",
        body=body or {},
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


@pytest.mark.parametrize(
    "field,value",
    [
        ("entry_id", "new..1"),
        ("body", {"b": "r"}),
        ("status", model.EntryStatus.IN_REVIEW),
    ],
)
def test_discarded_entry_has_event(field, value):
    entry = random_entry()
    entry.discard(user="alice@example.org", message="bad", timestamp=123.45)
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
    with pytest.raises(errors.DiscardedEntityError):
        setattr(entry, field, value)


@pytest.mark.parametrize(
    "field,value",
    [
        ("entry_id", "new..1"),
        ("body", {"b": "r"}),
        ("status", model.EntryStatus.IN_REVIEW),
    ],
)
def test_entry_update_updates(field, value):
    entry = random_entry(entry_id="test..2", body={"a": ["1", "e"]})

    previous_last_modified = entry.last_modified
    previous_last_modified_by = entry.last_modified_by
    message = f"Updated {field}"

    user = "Test User"

    setattr(entry, field, value)
    entry.stamp(user=user, message=message)

    assert getattr(entry, field) == value
    assert entry.last_modified > previous_last_modified
    assert entry.last_modified_by != previous_last_modified_by
    assert entry.last_modified_by == user
    assert entry.op == model.EntryOp.UPDATED
    assert entry.message == message
    assert entry.events[-1] == events.EntryUpdated(
        id=entry.id,
        entry_id=entry.entry_id,
        resource_id=entry.resource_id,
        user=entry.last_modified_by,
        timestamp=entry.last_modified,
        message=entry.message,
        version=2,
        body=entry.body,
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
