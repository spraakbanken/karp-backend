"""LexicalResource."""

import enum
import json
import typing
from typing import Any, Dict, Optional, Tuple

from karp.foundation import timings
from karp.foundation.entity import Entity
from karp.foundation.value_objects import PermissionLevel, unique_id
from karp.lex.domain import constraints, errors
from karp.lex.domain.entities import Entry, create_entry
from karp.lex.domain.value_objects import EntrySchema, ResourceConfig


class ResourceOp(enum.Enum):
    ADDED = "ADDED"
    UPDATED = "UPDATED"
    DELETED = "DELETED"


class Resource(Entity):
    DiscardedEntityError = errors.DiscardedEntityError
    resource_type: str = "resource"

    def __init__(
        self,
        *,
        id: unique_id.UniqueId,  # noqa: A002
        resource_id: str,
        name: str,
        config_str: str,
        message: str,
        table_name: str,
        version: int = 1,
        op: ResourceOp = ResourceOp.ADDED,
        is_published: bool = False,
        **kwargs,
    ):
        super().__init__(id=unique_id.UniqueId.validate(id), version=version, **kwargs)
        self._resource_id = resource_id
        self._name = name
        self.is_published = is_published
        self.config_str = config_str
        self.config = ResourceConfig.from_str(config_str)
        self._message = message
        self._op = op
        self._entry_schema = None
        self.table_name = table_name

    @property
    def resource_id(self) -> str:
        return self._resource_id

    @property
    def name(self):
        return self._name

    @property
    def message(self):
        return self._message

    @property
    def op(self):
        return self._op

    def publish(
        self,
        *,
        user: str,
        message: str,
        version: Optional[int],
        timestamp: Optional[float] = None,
    ):
        self._update_metadata(timestamp, user, message or "Published", version)
        self.is_published = True

    def unpublish(
        self,
        user: str,
        version: Optional[int],
    ):
        self._update_metadata(None, user, "Unpublished", version)
        self.is_published = False

    def update(
        self,
        *,
        name: str,
        config: dict[str, Any],
        user: str,
        version: Optional[int],
        timestamp: Optional[float] = None,
        message: Optional[str] = None,
    ) -> bool:
        if self.name == name and self.config == config:
            return False
        self._update_metadata(timestamp, user, message or "updating", version)
        self._name = name
        self.config = config
        return True

    def _update_metadata(
        self, timestamp: Optional[float], user: str, message: str, version: Optional[int]
    ):
        self._check_not_discarded()
        self._validate_version(version)
        self._last_modified = self._ensure_timestamp(timestamp)
        self._last_modified_by = user
        self._message = message
        self._op = ResourceOp.UPDATED
        self._increment_version()

    def discard(self, *, user: str, message: str, timestamp: Optional[float] = None):
        raise NotImplementedError()

    @property
    def entry_schema(self) -> EntrySchema:
        """Entry schema."""
        if self._entry_schema is None:
            self._entry_schema = EntrySchema.from_resource_config(self.config)
        return self._entry_schema

    def _validate_entry(self, entry: dict[str, Any]) -> dict[str, Any]:
        """Validate an entry against this resource's entry schema."""
        return self.entry_schema.validate_entry(entry)

    def create_entry_from_dict(
        self,
        entry_raw: dict[str, Any],
        *,
        user: str,
        id: unique_id.UniqueId,  # noqa: A002
        message: Optional[str] = None,
        timestamp: Optional[float] = None,
    ) -> Entry:
        """Create an entry for this resource."""
        self._check_not_discarded()

        return create_entry(
            self._validate_entry(entry_raw),
            resource_id=self.resource_id,
            last_modified_by=user,
            message=message,
            id=id,
            last_modified=timestamp,
        )

    def update_entry(
        self,
        *,
        entry: Entry,
        body: dict[str, Any],
        version: int,
        user: str,
        message: Optional[str] = None,
        timestamp: Optional[float] = None,
    ):
        """Create an entry for this resource."""
        self._check_not_discarded()
        entry.update_body(
            self._validate_entry(body),
            version=version,
            user=user,
            message=message,
            timestamp=timestamp,
        )

    def discard_entry(
        self,
        *,
        entry: Entry,
        version: int,
        user: str,
        message: Optional[str] = None,
        timestamp: Optional[float] = None,
    ):
        """Create an entry for this resource."""
        self._check_not_discarded()

        entry.discard(
            version=version,
            user=user,
            message=message,
            timestamp=timestamp,
        )


# ===== Factories =====


def create_resource(
    resource_id: str,
    config: ResourceConfig,
    name: Optional[str] = None,
    created_by: Optional[str] = None,
    user: Optional[str] = None,
    created_at: Optional[float] = None,
    id: unique_id.UniqueId = None,  # noqa: A002
    message: typing.Optional[str] = None,
) -> Resource:
    constraints.valid_resource_id(resource_id)
    name = name or resource_id

    id = id or unique_id.make_unique_id()  # noqa: A001
    table_name = f"{resource_id}_{id}"
    resource = Resource(
        id=id,
        resource_id=resource_id,
        name=name,
        config_str=config.model_dump_json(),
        table_name=table_name,
        message=message or "Resource added.",
        op=ResourceOp.ADDED,
        version=1,
        last_modified=created_at or timings.utc_now(),
        last_modified_by=user or created_by or "unknown",
    )
    return resource
