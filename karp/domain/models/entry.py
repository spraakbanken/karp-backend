"""Model for a lexical entry."""
import abc
import enum
from functools import singledispatch
import logging
from typing import Dict, Optional, List, Tuple
from uuid import UUID
from abc import abstractclassmethod

from karp.domain import constraints
from karp.domain.errors import ConfigurationError
from karp.domain.common import _now, _unknown_user
from karp.domain.models import event_handler
from karp.domain.models.entity import TimestampedVersionedEntity

from karp.utility import unique_id


logger = logging.getLogger("karp")


class EntryOp(enum.Enum):
    ADDED = "ADDED"
    DELETED = "DELETED"
    UPDATED = "UPDATED"


class EntryStatus(enum.Enum):
    IN_PROGRESS = "IN-PROGRESS"
    IN_REVIEW = "IN_REVIEW"
    OK = "OK"


class Entry(TimestampedVersionedEntity):
    class Discarded(TimestampedVersionedEntity.Discarded):
        def mutate(self, entry):
            super().mutate(entry)
            entry._op = EntryOp.DELETED
            entry._message = "Entry deleted." if self.message is None else self.message

    def __init__(
        self,
        *,
        entry_id: str,
        body: Dict,
        message: str,
        resource_id: str,
        status: EntryStatus = EntryStatus.IN_PROGRESS,  # IN-PROGRESS, IN-REVIEW, OK, PUBLISHED
        op: EntryOp = EntryOp.ADDED,
        version: int = 1,
        **kwargs,
        # version: int = 0
    ):
        super().__init__(version=version, **kwargs)
        self._entry_id = entry_id
        self._body = body
        self._op = op
        self._message = "Entry added." if message is None else message
        self._status = status
        self.resource_id = resource_id

    @property
    def entry_id(self):
        """The entry_id of this entry."""
        return self._entry_id

    @entry_id.setter
    def entry_id(self, entry_id: str):
        self._check_not_discarded()
        self._entry_id = constraints.length_gt_zero("entry_id", entry_id)

    @property
    def body(self):
        """The body of the entry."""
        return self._body

    @body.setter
    def body(self, body: Dict):
        self._check_not_discarded()
        self._body = body

    @property
    def op(self):
        """The latest operation of this entry."""
        return self._op

    @property
    def status(self):
        """The workflow status of this entry."""
        return self._status

    @status.setter
    def status(self, status: EntryStatus):
        """The workflow status of this entry."""
        self._check_not_discarded()
        self._status = status

    @property
    def message(self):
        """The message for the latest operation of this entry."""
        return self._message

    def discard(self, *, user: str, message: str = None):
        event = Entry.Discarded(
            entity_id=self.id,
            entity_last_modified=self.last_modified,
            user=user,
            message=message,
            entity_version=self.version,
        )
        event.mutate(self)
        event_handler.publish(event)

    def stamp(
        self,
        user: str,
        *,
        message: str = None,
        timestamp: float = _now,
        increment_version: bool = True,
    ):
        super().stamp(user, timestamp=timestamp, increment_version=increment_version)
        self._message = message
        self._op = EntryOp.UPDATED

    def __repr__(self) -> str:
        return f"Entry(id={self._id}, entry_id={self._entry_id}, version={self.version}, last_modified={self._last_modified}, body={self.body})"


# === Factories ===
def create_entry(
    entry_id: str,
    body: Dict,
    *,
    last_modified_by: str = None,
    message: Optional[str] = None,
) -> Entry:
    if not isinstance(entry_id, str):
        entry_id = str(entry_id)
    entry = Entry(
        entry_id=entry_id,
        body=body,
        message="Entry added." if not message else message,
        status=EntryStatus.IN_PROGRESS,
        op=EntryOp.ADDED,
        entity_id=unique_id.make_unique_id(),
        version=1,
        last_modified_by="Unknown user" if not last_modified_by else last_modified_by,
    )
    return entry


# === Repository ===


# class EntryRepositorySettings:
#     """Settings for an EntryRepository."""
#
#     pass
#
#
# @singledispatch
# def create_entry_repository(settings: EntryRepositorySettings) -> EntryRepository:
#     raise RuntimeError(f"Don't know how to handle {settings!r}")
