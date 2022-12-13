from typing import Dict

import pytest

from karp.lex.domain import errors, events
from karp.lex.domain import entities
from karp.foundation.value_objects import unique_id
from karp.tests import common_data

from karp.tests.unit.lex import factories


def random_entry(entry_id: str = None, body: Dict = None) -> entities.Entry:
    return entities.create_entry(
        entity_id=unique_id.make_unique_id(),
        repo_id=unique_id.make_unique_id(),
        # entry_id=entry_id or "a",
        body=body or {},
        message="add",
        last_modified_by="kristoff@example.com",
        last_modified=12345.67,
    )


def test_new_entry_has_event():
    entry = random_entry()
    assert entry.domain_events[-1] == events.EntryAdded(
        entity_id=entry.id,
        repo_id=entry.repo_id,
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
        timestamp=123.45,
    )
    assert entry.discarded
    assert entry.domain_events[-1] == events.EntryDeleted(
        entity_id=entry.id,
        # entry_id=entry.entry_id,
        repo_id=entry.repo_id,
        user=entry.last_modified_by,
        timestamp=entry.last_modified,
        message=entry.message,
        version=2,
    )


# @pytest.mark.parametrize(
#     "field,value",
#     [
#         ("entry_id", "new..1"),
#         # ("body", {"b": "r"}),
#         # ("status", entities.EntryStatus.IN_REVIEW),
#     ],
# )
# def test_entry_update_updates(field, value):
#     entry = random_entry(entry_id="test..2", body={"a": ["1", "e"]})

#     previous_last_modified = entry.last_modified
#     previous_last_modified_by = entry.last_modified_by
#     message = f"Updated {field}"

#     user = "Test User"

#     setattr(entry, field, value)
#     # entry.stamp(user=user, message=message)

#     assert getattr(entry, field) == value
#     assert entry.last_modified > previous_last_modified
#     assert entry.last_modified_by != previous_last_modified_by
#     assert entry.last_modified_by == user
#     assert entry.op == entities.EntryOp.UPDATED
#     assert entry.message == message
#     assert entry.domain_events[-1] == events.EntryUpdated(
#         entity_id=entry.id,
#         entry_id=entry.entry_id,
#         repo_id=entry.repo_id,
#         user=entry.last_modified_by,
#         timestamp=entry.last_modified,
#         message=entry.message,
#         version=2,
#         body=entry.body,
#     )


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
