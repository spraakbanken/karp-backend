from unittest import mock
import uuid

import pytest

from karp.domain.errors import (
    ConfigurationError,
    DiscardedEntityError,
)
from karp.domain.models.entry import (
    EntryStatus,
    create_entry,
    Entry,
    EntryOp,
    EntryRepository,
)


def test_entry_create():
    entry_id = "test..1"
    body = {"test": "test"}
    with mock.patch("karp.utility.time.utc_now", return_value=12345):
        entry = create_entry(entry_id, body)

    assert isinstance(entry, Entry)

    expected_history_id = None

    assert entry.id == uuid.UUID(str(entry.id), version=4)
    # assert entry.history_id == expected_history_id
    assert entry.status == EntryStatus.IN_PROGRESS
    assert entry.entry_id == entry_id
    assert entry.body == body

    assert int(entry.last_modified) == 12345
    assert entry.last_modified_by == "Unknown user"

    assert entry.op == EntryOp.ADDED
    assert entry.message == "Entry added."


@pytest.mark.parametrize(
    "field,value",
    [("entry_id", "new..1"), ("body", {"b": "r"}), ("status", EntryStatus.IN_REVIEW)],
)
def test_entry_update_updates(field, value):
    entry = create_entry("test..2", {"a": ["1", "e"]})

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
    assert entry.op == EntryOp.UPDATED
    assert entry.message == message


@pytest.mark.parametrize(
    "field,value",
    [("entry_id", "new..1"), ("body", {"b": "r"}), ("status", EntryStatus.IN_REVIEW)],
)
def test_entry_update_of_discarded_raises_(field, value):
    entry = create_entry("test..2", {"a": ["1", "e"]})

    previous_last_modified = entry.last_modified

    entry.discard(user="Admin")

    assert entry.discarded
    assert entry.last_modified > previous_last_modified
    assert entry.last_modified_by == "Admin"
    assert entry.op == EntryOp.DELETED
    assert entry.message == "Entry deleted."

    with pytest.raises(DiscardedEntityError):
        setattr(entry, field, value)


def test_entry_repository_create_raises_configuration_error_on_nonexisting_type():
    with pytest.raises(ConfigurationError):
        EntryRepository.create("non-existing", {})


def test_entry_repository_has_class_attribute():
    assert EntryRepository.type is None
