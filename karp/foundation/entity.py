"""Entity"""
import datetime  # noqa: I001
from typing import Optional, Union, List, Iterable

from deprecated import deprecated

from karp.foundation.errors import ConsistencyError
from karp.foundation import errors
from karp.lex_core.value_objects import UniqueId
from karp.foundation.timings import monotonic_utc_now


class Entity:
    DiscardedEntityError = errors.DiscardedEntityError

    def __init__(
        self,
        id: UniqueId,  # noqa: A002
        discarded: bool = False,
        aggregate_root=None,
    ) -> None:
        super().__init__()
        self._id = id
        self._discarded = discarded
        self._root = aggregate_root

    @property
    def id(self):
        """A unique identifier for the entity."""
        return self._id

    @property
    def entity_id(self):
        """A unique identifier for the entity."""
        return self._id

    @property
    def discarded(self) -> bool:
        """True if this entity is marked as deleted, otherwise False."""
        return self._discarded

    @property
    def root(self):
        """The aggregate root or self."""
        return self if self._root is None else self._root

    def _check_not_discarded(self):
        if self._discarded:
            raise self.DiscardedEntityError(
                f"Attempt to use {self!r}, entity_id = {self.entity_id}"
            )


class VersionedEntity(Entity):
    def __init__(
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

    def _increment_version(self):
        self._version += 1

    def _validate_version(self, version: int) -> None:
        if version != self.version:
            raise ConsistencyError(f"Entity version mismatch: {version} != {self.version}")


class TimestampedEntity(Entity):
    def __init__(
        self,
        id: UniqueId,  # noqa: A002
        last_modified: Optional[float] = None,
        last_modified_by: Optional[str] = None,
        discarded: bool = False,
    ) -> None:
        super().__init__(id=id, discarded=discarded)
        self._last_modified = self._ensure_timestamp(last_modified)
        self._last_modified_by = "Unknown user" if last_modified_by is None else last_modified_by

    @property
    def last_modified(self):
        """The time this entity was last modified."""
        return self._last_modified

    @property
    def last_modified_by(self):
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

    def _validate_last_modified(self, last_modified: float):
        if int(last_modified) != int(self.last_modified):
            raise ConsistencyError(
                f"Event entity last_modified mismatch: {last_modified} != {self.last_modified}"
            )


class TimestampedVersionedEntity(VersionedEntity, TimestampedEntity):
    def __init__(
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
