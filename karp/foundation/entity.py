import datetime
from typing import Optional, Union

from karp.foundation import errors
from karp.foundation.errors import ConsistencyError
from karp.foundation.timings import monotonic_utc_now
from karp.lex_core.value_objects import UniqueId


class Entity:
    DiscardedEntityError = errors.DiscardedEntityError

    def __init__(
        self,
        id: UniqueId,  # noqa: A002
        last_modified: Optional[float] = None,
        last_modified_by: Optional[str] = None,
        discarded: bool = False,
        *,
        version: int,
    ) -> None:
        self._id = id
        self._discarded = discarded
        self._last_modified = self._ensure_timestamp(last_modified)
        self._last_modified_by = "Unknown user" if last_modified_by is None else last_modified_by
        self._version = version

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

    def _check_not_discarded(self):
        if self._discarded:
            raise self.DiscardedEntityError(
                f"Attempt to use {self!r}, entity_id = {self.entity_id}"
            )

    def _increment_version(self):
        self._version += 1

    def _validate_version(self, version: int) -> None:
        if version != self.version:
            raise ConsistencyError(f"Entity version mismatch: {version} != {self.version}")

    @property
    def version(self) -> int:
        """An integer version for the entity."""
        return self._version
