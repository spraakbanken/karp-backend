"""Entity"""
from typing import Optional

from deprecated import deprecated

from karp.foundation.errors import ConsistencyError
from karp.foundation import errors
from karp.foundation import events
from karp.utility.time import monotonic_utc_now


class Entity(events.EventMixin):
    DiscardedEntityError = errors.DiscardedEntityError

    def __init__(self, entity_id, discarded: bool = False, aggregate_root=None):
        super().__init__()
        self._id = entity_id
        self._discarded = discarded
        self._root = aggregate_root

    def queue_event(self, event):
        self._record_event(event)

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

    def discard(self) -> None:
        self._discarded = True

    def _check_not_discarded(self):
        if self._discarded:
            raise self.DiscardedEntityError(f"Attempt to use {self!r}")

    def _validate_event_applicability(self, event):
        if event.entity_id != self.id:
            raise ConsistencyError(
                f"Event entity id mismatch: {event.entity_id} != {self.id}"
            )


class VersionedEntity(Entity):

    def __init__(self, entity_id, version: int, discarded: bool = False):
        super().__init__(entity_id, discarded=discarded)
        self._version = version

    @property
    def version(self) -> int:
        """An integer version for the entity."""
        return self._version

    def discard(self, version: int) -> None:
        self._validate_version(version)
        if self._discarded:
            return
        super().discard()
        self._increment_version()

    def update(self, version: int) -> None:
        self._check_not_discarded()
        self._validate_version(version)
        self._increment_version()

    def _increment_version(self):
        self._version += 1

    def _validate_version(self, version: int) -> None:
        if version != self.version:
            raise ConsistencyError(
                f"Entity version mismatch: {version} != {self.version}"
            )


class TimestampedEntity(Entity):

    def __init__(
        self,
        entity_id,
        last_modified: float = None,
        last_modified_by: str = None,
        discarded: bool = False,
    ) -> None:
        super().__init__(entity_id, discarded=discarded)
        self._last_modified = self._ensure_timestamp(last_modified)
        self._last_modified_by = (
            "Unknown user" if last_modified_by is None else last_modified_by
        )

    @property
    def last_modified(self):
        """The time this entity was last modified."""
        return self._last_modified

    @last_modified.setter
    @deprecated(version='6.0.7', reason='use update')
    def last_modified(self, timestamp: float):
        self._check_not_discarded()
        self._last_modified = timestamp

    @property
    def last_modified_by(self):
        """The time this entity was last modified."""
        return self._last_modified_by

    @last_modified_by.setter
    @deprecated(version='6.0.7', reason='use update')
    def last_modified_by(self, user):
        self._check_not_discarded()
        self._last_modified_by = user

    @deprecated(version='6.0.7', reason='use update')
    def stamp(self, user, *, timestamp: float = None):
        self._check_not_discarded()
        self._last_modified_by = user
        self._last_modified = monotonic_utc_now() if timestamp is None else timestamp

    def discard(self, *, user, last_modified: float, timestamp: float = None):
        self._check_not_discarded()
        self._validate_last_modified(last_modified)
        super.discard()
        self._last_modified_by = user
        self._last_modified = self._ensure_timestamp(timestamp)

    def update(self, *, user, last_modified: float, timestamp: float = None):
        self._check_not_discarded()
        self._validate_last_modified(last_modified)

        self._last_modified_by = user
        self._last_modified = self._ensure_timestamp(timestamp)

    def _ensure_timestamp(self, timestamp: Optional[float]) -> float:
        return monotonic_utc_now() if timestamp is None else timestamp

    def _validate_last_modified(self, last_modified: float):
        if int(last_modified) != int(self.last_modified):
            raise ConsistencyError(
                f"Event entity last_modified mismatch: {last_modified} != {self.last_modified}"
            )


class TimestampedVersionedEntity(VersionedEntity, TimestampedEntity):

    def __init__(
        self,
        entity_id,
        last_modified: float = None,
        last_modified_by: str = None,
        discarded: bool = False,
        *,
        version: int,
    ) -> None:
        super().__init__(entity_id, version=version, discarded=discarded)
        TimestampedEntity.__init__(
            self,
            entity_id=entity_id,
            discarded=discarded,
            last_modified=last_modified,
            last_modified_by=last_modified_by,
        )

#     @property
#     def last_modified(self):
#         """The time this entity was last modified."""
#         return self._last_modified
#
#     @last_modified.setter
#     def last_modified(self, timestamp: float):
#         self._check_not_discarded()
#         self._last_modified = timestamp
#
#     @property
#     def last_modified_by(self):
#         """The time this entity was last modified."""
#         return self._last_modified_by
#
#     @last_modified_by.setter
#     def last_modified_by(self, user: str):
#         self._check_not_discarded()
#         self._last_modified_by = user

    @deprecated(version='6.0.7', reason='use update')
    def stamp(self, user, *, timestamp: float = None, increment_version: bool = True):
        self._check_not_discarded()

        self._last_modified_by = user
        self._last_modified = monotonic_utc_now() if timestamp is None else timestamp
        if increment_version:
            self._increment_version()

    def discard(
        self,
        *,
        user: str,
        version: int,
        last_modified: float,
        timestamp: float = None,
    ) -> None:
        self._check_not_discarded()
        self._validate_version(version)
        self._validate_last_modified(last_modified)

        self._discarded = True
        self._last_modified_by = user
        self._last_modified = self._ensure_timestamp(timestamp)
        self._increment_version()

    def update(
        self,
        *,
        user: str,
        version: int,
        last_modified: float,
        timestamp: float = None,
    ) -> None:
        self._check_not_discarded()
        self._validate_version(version)
        self._validate_last_modified(last_modified)

        self._last_modified_by = user
        self._last_modified = self._ensure_timestamp(timestamp)
        self._increment_version()

