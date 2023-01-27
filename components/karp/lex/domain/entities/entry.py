"""Model for a lexical entry."""
import enum
import logging
import typing
from typing import Dict, List, Optional, Any

from deprecated import deprecated

from karp.foundation import constraints
from karp.lex.domain import errors, events
from karp.foundation.entity import TimestampedVersionedEntity
from karp.foundation.value_objects import unique_id

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
    DiscardedEntityError = errors.DiscardedEntityError

    def __init__(
        self,
        *,
        # entry_id: str,
        body: Dict,
        message: str,
        # resource_id: str,
        repository_id: unique_id.UniqueId,
        # IN-PROGRESS, IN-REVIEW, OK, PUBLISHED
        status: EntryStatus = EntryStatus.IN_PROGRESS,
        op: EntryOp = EntryOp.ADDED,
        version: int = 1,
        **kwargs,
        # version: int = 0
    ):
        super().__init__(version=version, **kwargs)
        # self._entry_id = entry_id
        self._body = body
        self._op = op
        self._message = "Entry added." if message is None else message
        # self.resource_id = resource_id
        self._status = status
        self._repo_id = repository_id

    @property
    def repo_id(self) -> unique_id.UniqueId:
        return self._repo_id

    # @property
    # def entry_id(self):
    #     """The entry_id of this entry."""
    #     return self._entry_id

    # @entry_id.setter
    # @deprecated(version="6.0.7", reason="use update")
    # def entry_id(self, entry_id: str):
    #     self._check_not_discarded()
    #     self._entry_id = constraints.length_gt_zero("entry_id", entry_id)

    @property
    def body(self):
        """The body of the entry."""
        return self._body

    # @body.setter
    # @deprecated(version="6.0.7", reason="use update")
    def update_body(
        self,
        body: Dict,
        *,
        user: str,
        message: Optional[str] = None,
        timestamp: Optional[float] = None,
    ):
        self._check_not_discarded()
        self._body = self._update_field(body, user, timestamp)
        self._message = message or "Entry updated"
        self._op = EntryOp.UPDATED
        self._record_event(
            events.EntryUpdated(
                entity_id=self.id,
                timestamp=self.last_modified,
                user=self.last_modified_by,
                version=self.version,
                body=self.body,
                repo_id=self.repo_id,
                message=self.message,
            )
        )

    @property
    def op(self):
        """The latest operation of this entry."""
        return self._op

    @property
    def status(self):
        """The workflow status of this entry."""
        return self._status

    # @status.setter
    # @deprecated(version="6.0.7", reason="use update")
    # def status(self, status: EntryStatus):
    #     """The workflow status of this entry."""
    #     self._check_not_discarded()
    #     self._status = status

    @property
    def message(self):
        """The message for the latest operation of this entry."""
        return self._message

    def dict(self) -> Dict[str, Any]:
        return {
            # "entry_id": self._entry_id,
            "entity_id": self.entity_id,
            "resource": "",
            "version": self._version,
            "entry": self._body,
            "last_modified": self._last_modified,
            "last_modified_by": self._last_modified_by,
            "discarded": self._discarded,
            "message": self._message,
        }

    def discard(
        self,
        *,
        user: str,
        timestamp: Optional[float] = None,
        message: Optional[str] = None,
    ):
        if self._discarded:
            return
        self._op = EntryOp.DELETED
        self._message = message or "Entry deleted."
        self._discarded = self._update_field(True, user, timestamp)
        self._record_event(
            events.EntryDeleted(
                entity_id=self.id,
                # entry_id=self.entry_id,
                timestamp=self.last_modified,
                user=user,
                message=self._message,
                version=self.version,
                repo_id=self.repo_id,
            )
        )

    def _update_field(self, arg0, user: str, timestamp: Optional[float]):
        result = arg0
        self._last_modified_by = user
        self._last_modified = self._ensure_timestamp(timestamp)
        self._increment_version()
        return result

    def __repr__(self) -> str:
        return f"Entry(id={self._id}, version={self.version}, last_modified={self._last_modified}, body={self.body})"


# === Factories ===
def create_entry(
    # entry_id: str,
    body: Dict,
    *,
    entity_id: unique_id.UniqueId,
    repo_id: unique_id.UniqueId,
    last_modified_by: str = None,
    message: Optional[str] = None,
    last_modified: typing.Optional[float] = None,
) -> Entry:
    # if not isinstance(entry_id, str):
    #     entry_id = str(entry_id)
    entry = Entry(
        # entry_id=entry_id,
        body=body,
        message="Entry added." if not message else message,
        status=EntryStatus.IN_PROGRESS,
        op=EntryOp.ADDED,
        # entity_id=unique_id.make_unique_id(),
        version=1,
        last_modified_by="Unknown user" if not last_modified_by else last_modified_by,
        repository_id=repo_id,
        entity_id=entity_id,
        last_modified=last_modified,
    )
    entry.queue_event(
        events.EntryAdded(
            repo_id=repo_id,
            entity_id=entry.id,
            # entry_id=entry.entry_id,
            body=entry.body,
            message=entry.message or "",
            user=entry.last_modified_by,
            timestamp=entry.last_modified,
        )
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
