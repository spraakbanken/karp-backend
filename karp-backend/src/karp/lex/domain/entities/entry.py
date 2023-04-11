"""Model for a lexical entry."""
import enum  # noqa: I001
import logging
import typing
from typing import Dict, Optional, Any, Tuple


from karp.lex.domain import errors, events
from karp.foundation.entity import TimestampedVersionedEntity
from karp.lex_core.value_objects import UniqueId, unique_id

logger = logging.getLogger("karp")


class EntryOp(enum.Enum):  # noqa: D101
    ADDED = "ADDED"
    DELETED = "DELETED"
    UPDATED = "UPDATED"


class EntryStatus(enum.Enum):  # noqa: D101
    IN_PROGRESS = "IN-PROGRESS"
    IN_REVIEW = "IN_REVIEW"
    OK = "OK"


class Entry(TimestampedVersionedEntity):  # noqa: D101
    DiscardedEntityError = errors.DiscardedEntityError

    def __init__(  # noqa: D107, ANN204
        self,
        *,
        id: UniqueId,  # noqa: A002
        body: Dict,
        message: str,
        repository_id: unique_id.UniqueId,
        # IN-PROGRESS, IN-REVIEW, OK, PUBLISHED
        status: EntryStatus = EntryStatus.IN_PROGRESS,
        op: EntryOp = EntryOp.ADDED,
        version: int = 1,
        **kwargs,  # noqa: ANN003
    ):
        super().__init__(id=UniqueId.validate(id), version=version, **kwargs)
        self._body = body
        self._op = op
        self._message = "Entry added." if message is None else message
        self._status = status
        self._repo_id = repository_id

    @property
    def repo_id(self) -> unique_id.UniqueId:  # noqa: D102
        return self._repo_id

    @property
    def body(self):  # noqa: ANN201
        """The body of the entry."""
        return self._body

    def update_body(  # noqa: D102
        self,
        body: Dict,
        *,
        version: int,
        user: str,
        message: Optional[str] = None,
        timestamp: Optional[float] = None,
    ) -> list[events.Event]:
        self._check_not_discarded()
        if self._body == body:
            return []
        self._check_version(version)
        self._body = self._update_field(body, user, timestamp)
        self._message = message or "Entry updated"
        self._op = EntryOp.UPDATED
        return [
            events.EntryUpdated(
                id=self.id,
                timestamp=self.last_modified,
                user=self.last_modified_by,
                version=self.version,
                body=self.body,
                repoId=self.repo_id,
                message=self.message,
            )
        ]

    @property
    def op(self):  # noqa: ANN201
        """The latest operation of this entry."""
        return self._op

    @property
    def status(self):  # noqa: ANN201
        """The workflow status of this entry."""
        return self._status

    @property
    def message(self):  # noqa: ANN201
        """The message for the latest operation of this entry."""
        return self._message

    def serialize(self) -> Dict[str, Any]:  # noqa: D102
        return {
            "id": self.id,
            "resource": "",
            "version": self._version,
            "entry": self._body,
            "lastModified": self._last_modified,
            "lastModifiedBy": self._last_modified_by,
            "discarded": self._discarded,
            "message": self._message,
        }

    def discard(  # noqa: D102
        self,
        *,
        version: int,
        user: str,
        timestamp: Optional[float] = None,
        message: Optional[str] = None,
    ) -> list[events.Event]:
        if self._discarded:
            return []
        self._check_not_discarded()
        self._check_version(version)
        self._op = EntryOp.DELETED
        self._message = message or "Entry deleted."
        self._discarded = self._update_field(True, user, timestamp)
        return [
            events.EntryDeleted(
                id=self.id,
                # entry_id=self.entry_id,
                timestamp=self.last_modified,
                user=user,
                message=self._message,
                version=self.version,
                repoId=self.repo_id,
            )
        ]

    def _check_version(self, version: int) -> None:
        if self.version != version:
            msg = f"Expecting version '{self.version}', got '{version}'"
            raise errors.UpdateConflict(msg)

    def _update_field(  # noqa: ANN202
        self, arg0, user: str, timestamp: Optional[float]
    ):
        result = arg0
        self._last_modified_by = user
        self._last_modified = self._ensure_timestamp(timestamp)
        self._increment_version()
        return result

    def __repr__(self) -> str:  # noqa: D105
        return f"Entry(id={self._id}, version={self.version}, last_modified={self._last_modified}, body={self.body})"


def create_entry(  # noqa: D103
    body: Dict,
    *,
    id: unique_id.UniqueId,  # noqa: A002
    repo_id: unique_id.UniqueId,
    last_modified_by: str = None,
    message: Optional[str] = None,
    last_modified: typing.Optional[float] = None,
) -> Tuple[Entry, list[events.Event]]:
    entry = Entry(
        body=body,
        message="Entry added." if not message else message,
        status=EntryStatus.IN_PROGRESS,
        op=EntryOp.ADDED,
        # id=unique_id.make_unique_id(),
        version=1,
        last_modified_by="Unknown user" if not last_modified_by else last_modified_by,
        repository_id=repo_id,
        id=id,
        last_modified=last_modified,
    )
    event = events.EntryAdded(
        repoId=repo_id,
        id=entry.id,
        body=entry.body,
        message=entry.message or "",
        user=entry.last_modified_by,
        timestamp=entry.last_modified,
    )

    return entry, [event]
