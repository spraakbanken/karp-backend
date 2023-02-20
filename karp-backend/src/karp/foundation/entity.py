"""Entity"""  # noqa: D400, D415
import datetime  # noqa: I001
from typing import Optional, Union

from deprecated import deprecated  # noqa: F401

from karp.foundation.errors import ConsistencyError
from karp.foundation import errors
from karp.foundation import events
from karp.lex_core.value_objects import UniqueId
from karp.utility.time import monotonic_utc_now


class Entity(events.EventMixin):  # noqa: D101
    DiscardedEntityError = errors.DiscardedEntityError

    def __init__(  # noqa: D107
        self,
        id: UniqueId,  # noqa: A002
        discarded: bool = False,
        aggregate_root=None,
    ) -> None:
        super().__init__()
        self._id = id
        self._discarded = discarded
        self._root = aggregate_root

    def queue_event(self, event):  # noqa: ANN201, D102
        self._record_event(event)

    @property
    def id(self):  # noqa: A003, ANN201
        """A unique identifier for the entity."""
        return self._id

    @property
    def entity_id(self):  # noqa: ANN201
        """A unique identifier for the entity."""
        return self._id

    @property
    def discarded(self) -> bool:
        """True if this entity is marked as deleted, otherwise False."""
        return self._discarded

    @property
    def root(self):  # noqa: ANN201
        """The aggregate root or self."""
        return self if self._root is None else self._root

    def _check_not_discarded(self):  # noqa: ANN202
        if self._discarded:
            raise self.DiscardedEntityError(
                f"Attempt to use {self!r}, entity_id = {self.entity_id}"
            )

    def _validate_event_applicability(self, event):  # noqa: ANN202
        if event.entity_id != self.id:
            raise ConsistencyError(
                f"Event entity id mismatch: {event.entity_id} != {self.id}"
            )


class VersionedEntity(Entity):  # noqa: D101
    def __init__(  # noqa: D107
        self,
        id: UniqueId,  # noqa: A002
        version: int,
        discarded: bool = False,
    ) -> None:
        super().__init__(id, discarded=discarded)
        self._version = version

    @property
    def version(self) -> int:
        """An integer version for the entity."""
        return self._version

    def _increment_version(self):  # noqa: ANN202
        self._version += 1

    def _validate_version(self, version: int) -> None:
        if version != self.version:
            raise ConsistencyError(
                f"Entity version mismatch: {version} != {self.version}"
            )


class TimestampedEntity(Entity):  # noqa: D101
    def __init__(  # noqa: D107
        self,
        id: UniqueId,  # noqa: A002
        last_modified: Optional[float] = None,
        last_modified_by: Optional[str] = None,
        discarded: bool = False,
    ) -> None:
        super().__init__(id=id, discarded=discarded)
        self._last_modified = self._ensure_timestamp(last_modified)
        self._last_modified_by = (
            "Unknown user" if last_modified_by is None else last_modified_by
        )

    @property
    def last_modified(self):  # noqa: ANN201
        """The time this entity was last modified."""
        return self._last_modified

    @property
    def last_modified_by(self):  # noqa: ANN201
        """The time this entity was last modified."""
        return self._last_modified_by

    def _ensure_timestamp(
        self, timestamp: Optional[Union[float, datetime.datetime, str]]
    ) -> float:
        if isinstance(timestamp, datetime.datetime):
            return timestamp.timestamp()
        elif isinstance(timestamp, str):
            return datetime.datetime.fromisoformat(timestamp).timestamp()
        return monotonic_utc_now() if timestamp is None else timestamp

    def _validate_last_modified(self, last_modified: float):  # noqa: ANN202
        if int(last_modified) != int(self.last_modified):
            raise ConsistencyError(
                f"Event entity last_modified mismatch: {last_modified} != {self.last_modified}"
            )


class TimestampedVersionedEntity(VersionedEntity, TimestampedEntity):  # noqa: D101
    def __init__(  # noqa: D107
        self,
        id: UniqueId,  # noqa: A002
        last_modified: Optional[float] = None,
        last_modified_by: Optional[str] = None,
        discarded: bool = False,
        *,
        version: int,
    ) -> None:
        super().__init__(id, version=version, discarded=discarded)
        TimestampedEntity.__init__(
            self,
            id=id,
            discarded=discarded,
            last_modified=last_modified,
            last_modified_by=last_modified_by,
        )
