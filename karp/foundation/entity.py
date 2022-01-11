"""Entity"""
from karp.domain.common import _now, _unknown_user
from karp.foundation.errors import ConsistencyError
from karp.foundation import errors
from karp.domain.models.events import DomainEvent
from karp.foundation import events
from karp.utility.time import monotonic_utc_now


class Entity(events.EventMixin):
    DiscardedEntityError = errors.DiscardedEntityError

    class Discarded(DomainEvent):
        def mutate(self, obj):
            obj._validate_event_applicability(self)
            obj._discarded = True

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
    def discarded(self) -> bool:
        """True if this entity is marked as deleted, otherwise False."""
        return self._discarded

    @property
    def root(self):
        """The aggregate root or self."""
        return self if self._root is None else self._root

    def _check_not_discarded(self):
        if self._discarded:
            raise self.DiscardedEntityError(f"Attempt to use {self!r}")

    def _validate_event_applicability(self, event):
        if event.entity_id != self.id:
            raise ConsistencyError(
                f"Event entity id mismatch: {event.entity_id} != {self.id}"
            )


class VersionedEntity(Entity):
    class Discarded(Entity.Discarded):
        def mutate(self, obj):
            super().mutate(obj)
            obj._increment_version()

    class Stamped(DomainEvent):
        def mutate(self, obj):
            obj._validate_event_applicability(self)
            obj._increment_version()

    def __init__(self, entity_id, version: int, discarded: bool = False):
        super().__init__(entity_id, discarded=discarded)
        self._version = version

    @property
    def version(self) -> int:
        """An integer version for the entity."""
        return self._version

    def discard(self, version: int) -> None:
        if version != self.version:
            raise ConsistencyError(
                f"Entity version mismatch: {version} != {self.version}"
            )
        super().discard()
        self._increment_version()

    def _increment_version(self):
        self._version += 1

    def _validate_event_applicability(self, event):
        if event.entity_id != self.id:
            raise ConsistencyError(
                f"Event entity id mismatch: {event.entity_id} != {self.id}"
            )
        if event.entity_version != self.version:
            raise ConsistencyError(
                f"Event entity version mismatch: {event.entity_version} != {self.version}"
            )


class TimestampedEntity(Entity):
    class Discarded(Entity.Discarded):
        def mutate(self, obj):
            super().mutate(obj)
            obj._last_modified = self.timestamp
            obj._last_modified_by = self.user

    class Stamped(DomainEvent):
        def mutate(self, obj):
            obj._validate_event_applicability(self)
            obj._last_modified = self.timestamp
            obj._last_modified_by = self.user

    def __init__(
        self,
        entity_id,
        last_modified: float = _now,
        last_modified_by: str = _unknown_user,
        discarded: bool = False,
    ) -> None:
        super().__init__(entity_id, discarded=discarded)
        self._last_modified = (
            monotonic_utc_now() if last_modified is _now else last_modified
        )
        self._last_modified_by = (
            _unknown_user if last_modified_by is _unknown_user else last_modified_by
        )

    @property
    def last_modified(self):
        """The time this entity was last modified."""
        return self._last_modified

    @last_modified.setter
    def last_modified(self, timestamp: float):
        self._check_not_discarded()
        self._last_modified = timestamp

    @property
    def last_modified_by(self):
        """The time this entity was last modified."""
        return self._last_modified_by

    @last_modified_by.setter
    def last_modified_by(self, user):
        self._check_not_discarded()
        self._last_modified_by = user

    def stamp(self, user, *, timestamp: float = _now):
        self._check_not_discarded()
        self._last_modified_by = user
        self._last_modified = monotonic_utc_now() if timestamp is _now else timestamp

    def _validate_event_applicability(self, event):
        if event.entity_id != self.id:
            raise ConsistencyError(
                f"Event entity id mismatch: {event.entity_id} != {self.id}"
            )
        if event.entity_last_modified != self.last_modified:
            raise ConsistencyError(
                f"Event entity last_modified mismatch: {event.entity_last_modified} != {self.last_modified}"
            )


class TimestampedVersionedEntity(VersionedEntity, TimestampedEntity):
    class Discarded(VersionedEntity.Discarded, TimestampedEntity.Discarded):
        def mutate(self, obj):
            super().mutate(obj)

    class Stamped(VersionedEntity.Stamped, TimestampedEntity.Stamped):
        def __init__(self, *, increment_version: bool = True, **kwargs):
            super().__init__(**kwargs)
            self.increment_version = increment_version

        def mutate(self, obj):
            obj._validate_event_applicability(self)
            obj._last_modified = self.timestamp
            obj._last_modified_by = self.user
            if self.increment_version:
                obj._increment_version()

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
        self._last_modified = (
            monotonic_utc_now() if last_modified is None else last_modified
        )
        self._last_modified_by = (
            _unknown_user if last_modified_by is None else last_modified_by
        )

    @property
    def last_modified(self):
        """The time this entity was last modified."""
        return self._last_modified

    @last_modified.setter
    def last_modified(self, timestamp: float):
        self._check_not_discarded()
        self._last_modified = timestamp

    @property
    def last_modified_by(self):
        """The time this entity was last modified."""
        return self._last_modified_by

    @last_modified_by.setter
    def last_modified_by(self, user: str):
        self._check_not_discarded()
        self._last_modified_by = user

    def stamp(self, user, *, timestamp: float = _now, increment_version: bool = True):
        self._check_not_discarded()
        event = TimestampedVersionedEntity.Stamped(
            timestamp=timestamp,
            entity_id=self.id,
            entity_version=self.version,
            entity_last_modified=self.last_modified,
            user=user,
            increment_version=increment_version,
        )
        event.mutate(self)
        # self._last_modified_by = user
        # self._last_modified = monotonic_utc_now() if timestamp is _now else timestamp
        # if increment_version:
        #     self._increment_version()

    def _validate_event_applicability(self, event):
        VersionedEntity._validate_event_applicability(self, event)
        TimestampedEntity._validate_event_applicability(self, event)
