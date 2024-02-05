"""Model for a lexical entry."""
import enum  # noqa: I001
import logging
import typing
from typing import Dict, Optional, Any, Tuple


from karp.lex.domain import errors
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
        resource_id: str,
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
        self._resource_id = resource_id

    @property
    def resource_id(self) -> str:  # noqa: D102
        return self._resource_id

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
    ):
        self._check_not_discarded()
        if self._body == body:
            return
        self._check_version(version)
        self._body = self._update_field(body, user, timestamp)
        self._message = message or "Entry updated"
        self._op = EntryOp.UPDATED

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
    ):
        if self._discarded:
            return []
        self._check_not_discarded()
        self._check_version(version)
        self._op = EntryOp.DELETED
        self._message = message or "Entry deleted."
        self._discarded = self._update_field(True, user, timestamp)

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
    resource_id: str,
    last_modified_by: Optional[str] = None,
    message: Optional[str] = None,
    last_modified: typing.Optional[float] = None,
) -> Entry:
    return Entry(
        body=body,
        message="Entry added." if not message else message,
        status=EntryStatus.IN_PROGRESS,
        op=EntryOp.ADDED,
        # id=unique_id.make_unique_id(),
        version=1,
        last_modified_by="Unknown user" if not last_modified_by else last_modified_by,
        resource_id=resource_id,
        id=id,
        last_modified=last_modified,
    )
