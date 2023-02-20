from typing import Tuple

from karp.lex.domain import entities, events
from karp.lex_core.value_objects import unique_id


def random_entry(
    entry_id: str = None, body: dict = None
) -> Tuple[entities.Entry, list[events.Event]]:
    return entities.create_entry(
        id=unique_id.make_unique_id(),
        repo_id=unique_id.make_unique_id(),
        # entry_id=entry_id or "a",
        body=body or {},
        message="add",
        last_modified_by="kristoff@example.com",
        last_modified=12345.67,
    )


def test_new_entry_has_event():  # noqa: ANN201
    entry, domain_events = random_entry()
    assert domain_events[-1] == events.EntryAdded(
        id=entry.id,
        repoId=entry.repo_id,
        body=entry.body,
        user=entry.last_modified_by,
        timestamp=entry.last_modified,
        message=entry.message,
    )


def test_discarded_entry_has_event():  # noqa: ANN201
    entry, _ = random_entry()
    domain_events = entry.discard(
        user="alice@example.org",
        message="bad",
        timestamp=123.45,
    )
    assert entry.discarded
    assert domain_events[-1] == events.EntryDeleted(
        id=entry.id,
        # entry_id=entry.entry_id,
        repoId=entry.repo_id,
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
#         id=entry.id,
#         entry_id=entry.entry_id,
#         repoId=entry.repo_id,
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
