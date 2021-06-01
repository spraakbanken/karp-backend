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


def test_entry_repository_create_raises_configuration_error_on_nonexisting_type():
    with pytest.raises(ConfigurationError):
        EntryRepository.create("non-existing", {})
