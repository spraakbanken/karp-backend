"""LexicalResource."""
import enum
import typing
from typing import Any, Dict, Optional, Tuple

from karp.foundation import timings
from karp.foundation.entity import Entity
from karp.foundation.value_objects import PermissionLevel, unique_id
from karp.lex.domain import constraints, errors
from karp.lex.domain.entities import Entry, create_entry
from karp.lex.domain.value_objects import EntrySchema


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
        config: Dict[str, Any],
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
        self.config = config
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
        version: int,
        timestamp: Optional[float] = None,
    ):
        self._update_metadata(timestamp, user, message or "Published", version)
        self.is_published = True

    def update(
        self,
        *,
        name: str,
        config: dict[str, Any],
        user: str,
        version: int,
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
        self, timestamp: Optional[float], user: str, message: str, version: int
    ):
        self._check_not_discarded()
        self._validate_version(version)
        self._last_modified = self._ensure_timestamp(timestamp)
        self._last_modified_by = user
        self._message = message
        self._op = ResourceOp.UPDATED
        self._increment_version()

    def discard(self, *, user: str, message: str, timestamp: Optional[float] = None):
        self._op = ResourceOp.DELETED
        self._message = message or "Entry deleted."
        self._discarded = True
        self._last_modified_by = user
        self._last_modified = timestamp or timings.utc_now()
        self._version += 1

    @property
    def entry_schema(self) -> EntrySchema:
        """Entry schema."""
        if self._entry_schema is None:
            self._entry_schema = EntrySchema.from_resource_config(self.config)
        return self._entry_schema

    def serialize(self) -> dict[str, Any]:
        """Serialize resource to camelCased dict."""
        return {
            "id": self.id,
            "resourceId": self.resource_id,
            "name": self.name,
            "version": self.version,
            "lastModified": self.last_modified,
            "lastModifiedBy": self.last_modified_by,
            "op": self.op,
            "message": self.message,
            "tableName": self.table_name,
            "isPublished": self.is_published,
            "discarded": self.discarded,
            "resource_type": self.resource_type,
            "config": self.config,
        }

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
    config: dict[str, Any],
    table_name: str,
    created_by: Optional[str] = None,
    user: Optional[str] = None,
    created_at: Optional[float] = None,
    id: unique_id.UniqueId = None,  # noqa: A002
    resource_id: typing.Optional[str] = None,
    message: typing.Optional[str] = None,
    name: typing.Optional[str] = None,
) -> Resource:
    resource_id_in_config: Optional[str] = config.pop("resource_id", None)
    resource_id_resolved = resource_id or resource_id_in_config
    if resource_id_resolved is None:
        raise ValueError("resource_id is missing")
    constraints.valid_resource_id(resource_id_resolved)
    name_in_config: str = config.pop("resource_name", None)
    resource_name: str = name or name_in_config or resource_id_resolved  # type: ignore [assignment]

    resource = Resource(
        id=id or unique_id.make_unique_id(),
        resource_id=resource_id_resolved,
        name=resource_name,
        config=config,
        table_name=table_name,
        message=message or "Resource added.",
        op=ResourceOp.ADDED,
        version=1,
        last_modified=created_at or timings.utc_now(),
        last_modified_by=user or created_by or "unknown",
    )
    return resource
