"""LexicalResource."""
import enum
import typing
from typing import Any, Dict, Optional, Tuple

from karp import timings
from karp.foundation.entity import Entity, TimestampedVersionedEntity
from karp.foundation.value_objects import PermissionLevel
from karp.lex.domain import constraints, errors, events
from karp.lex.domain.entities import Entry, create_entry
from karp.lex.domain.value_objects import EntrySchema
from karp.lex_core.value_objects import unique_id


class ResourceOp(enum.Enum):  # noqa: D101
    ADDED = "ADDED"
    UPDATED = "UPDATED"
    DELETED = "DELETED"


class Resource(TimestampedVersionedEntity):  # noqa: D101
    DiscardedEntityError = errors.DiscardedEntityError
    resource_type: str = "resource"

    def __init__(  # noqa: D107, ANN204
        self,
        *,
        id: unique_id.UniqueId,  # noqa: A002
        resource_id: str,
        name: str,
        config: Dict[str, Any],
        message: str,
        entry_repo_id: unique_id.UniqueId,
        version: int = 1,
        op: ResourceOp = ResourceOp.ADDED,
        is_published: bool = False,
        **kwargs,  # noqa: ANN003
    ):
        super().__init__(id=unique_id.UniqueId.validate(id), version=version, **kwargs)
        self._resource_id = resource_id
        self._name = name
        self.is_published = is_published
        self.config = config
        self._message = message
        self._op = op
        self._releases = []
        self._entry_schema = None
        self._entry_repo_id = unique_id.UniqueId.validate(entry_repo_id)

    @property
    def resource_id(self) -> str:  # noqa: D102
        return self._resource_id

    @property
    def entry_repository_id(self) -> unique_id.UniqueId:  # noqa: D102
        return self._entry_repo_id

    @property
    def name(self):  # noqa: ANN201, D102
        return self._name

    @property
    def generators(self) -> dict[str, str]:
        """Generators for entry fields."""
        return self.config.get("generators", {})

    @property
    def message(self):  # noqa: ANN201, D102
        return self._message

    @property
    def releases(self):  # noqa: ANN201
        """Releases for this resource."""
        return self._releases

    @property
    def op(self):  # noqa: ANN201, D102
        return self._op

    def publish(  # noqa: D102
        self,
        *,
        user: str,
        message: str,
        version: int,
        timestamp: Optional[float] = None,
    ) -> list[events.Event]:
        self._update_metadata(timestamp, user, message or "Published", version)
        self.is_published = True
        return [
            events.ResourcePublished(
                id=self.id,
                resourceId=self.resource_id,
                entryRepoId=self.entry_repository_id,
                timestamp=self.last_modified,
                user=self.last_modified_by,
                version=self.version,
                name=self.name,
                config=self.config,
                message=self.message,
            )
        ]

    def set_entry_repo_id(  # noqa: ANN201, D102
        self,
        *,
        entry_repo_id: unique_id.UniqueId,
        user: str,
        version: int,
        message: str | None = None,
        timestamp: Optional[float] = None,
    ):
        self._update_metadata(
            timestamp, user, message or "entry repo id updated", version=version
        )
        self._entry_repo_id = entry_repo_id
        return [
            events.ResourceUpdated(
                id=self.id,
                resourceId=self.resource_id,
                entryRepoId=self.entry_repository_id,
                timestamp=self.last_modified,
                user=self.last_modified_by,
                version=self.version,
                name=self.name,
                config=self.config,
                message=self.message,
            )
        ]

    def set_resource_id(  # noqa: D102
        self,
        *,
        resource_id: str,
        user: str,
        version: int,
        timestamp: Optional[float] = None,
        message: Optional[str] = None,
    ) -> list[events.Event]:
        self._update_metadata(timestamp, user, message or "setting resource_id", version)
        self._resource_id = resource_id
        return [
            events.ResourceUpdated(
                id=self.id,
                resourceId=self.resource_id,
                entryRepoId=self.entry_repository_id,
                timestamp=self.last_modified,
                user=self.last_modified_by,
                version=self.version,
                name=self.name,
                config=self.config,
                message=self.message,
            )
        ]

    def update(  # noqa: D102
        self,
        *,
        name: str,
        config: dict[str, Any],
        user: str,
        version: int,
        timestamp: Optional[float] = None,
        message: Optional[str] = None,
    ) -> list[events.Event]:
        if self.name == name and self.config == config:
            return []
        self._update_metadata(timestamp, user, message or "updating", version)
        self._name = name
        self.config = config
        return [
            events.ResourceUpdated(
                id=self.id,
                resourceId=self.resource_id,
                entryRepoId=self.entry_repository_id,
                timestamp=self.last_modified,
                user=self.last_modified_by,
                version=self.version,
                name=self.name,
                config=self.config,
                message=self.message,
            )
        ]

    def set_config(  # noqa: D102
        self,
        *,
        config: dict[str, Any],
        user: str,
        version: int,
        timestamp: Optional[float] = None,
        message: Optional[str] = None,
    ) -> list[events.Event]:
        if self.config == config:
            return []
        self._update_metadata(timestamp, user, message or "setting config", version)
        self.config = config
        return [
            events.ResourceUpdated(
                id=self.id,
                resourceId=self.resource_id,
                entryRepoId=self.entry_repository_id,
                timestamp=self.last_modified,
                user=self.last_modified_by,
                version=self.version,
                name=self.name,
                config=self.config,
                message=self.message,
            )
        ]

    def _update_metadata(  # noqa: ANN202
        self, timestamp: Optional[float], user: str, message: str, version: int
    ):
        self._check_not_discarded()
        self._validate_version(version)
        self._last_modified = self._ensure_timestamp(timestamp)
        self._last_modified_by = user
        self._message = message
        self._op = ResourceOp.UPDATED
        self._increment_version()

    def release_with_name(self, name: str):  # noqa: ANN201, D102
        self._check_not_discarded()
        raise NotImplementedError()

    def discard(  # noqa: D102
        self, *, user: str, message: str, timestamp: Optional[float] = None
    ) -> list[events.Event]:
        self._op = ResourceOp.DELETED
        self._message = message or "Entry deleted."
        self._discarded = True
        self._last_modified_by = user
        self._last_modified = timestamp or timings.utc_now()
        self._version += 1
        return [
            events.ResourceDiscarded(
                id=self.id,
                version=self.version,
                timestamp=self.last_modified,
                user=self.last_modified_by,
                message=self.message,
                resourceId=self.resource_id,
                name=self.name,
                config=self.config,
            )
        ]

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
            "entryRepositoryId": self.entry_repository_id,
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
    ) -> Tuple[Entry, list[events.Event]]:
        """Create an entry for this resource."""
        self._check_not_discarded()

        return create_entry(
            self._validate_entry(entry_raw),
            repo_id=self.entry_repository_id,
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
    ) -> list[events.Event]:
        """Create an entry for this resource."""
        self._check_not_discarded()

        return entry.update_body(
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
    ) -> list[events.Event]:
        """Create an entry for this resource."""
        self._check_not_discarded()

        return entry.discard(
            version=version,
            user=user,
            message=message,
            timestamp=timestamp,
        )

    def is_protected(self, level: PermissionLevel):  # noqa: ANN201
        """
        Level can be READ, WRITE or ADMIN
        """  # noqa: D200, D400, D212, D415
        protection = self.config.get("protected", {})
        return level == "WRITE" or level == "ADMIN" or protection.get("read")


# ===== Entities =====
class Release(Entity):  # noqa: D101
    def __init__(  # noqa: D107
        self,
        name: str,
        publication_date: float,
        description: str,
        **kwargs,  # noqa: ANN003
    ) -> None:
        super().__init__(**kwargs)
        self._name = name
        self._publication_date = publication_date
        self._description = description

    @property
    def name(self) -> str:
        """The name of this release."""
        return self._name

    @property
    def publication_date(self) -> float:
        """The publication of this release."""
        return self._publication_date

    @property
    def description(self) -> str:
        """The description of this release."""
        return self._description


# ===== Factories =====


def create_resource(  # noqa: D103
    config: dict[str, Any],
    entry_repo_id: unique_id.UniqueId,
    created_by: Optional[str] = None,
    user: Optional[str] = None,
    created_at: Optional[float] = None,
    id: unique_id.UniqueId = None,  # noqa: A002
    resource_id: typing.Optional[str] = None,
    message: typing.Optional[str] = None,
    name: typing.Optional[str] = None,
) -> Tuple[Resource, list[events.Event]]:
    resource_id_in_config: Optional[str] = config.pop("resource_id", None)
    resource_id_resolved = resource_id or resource_id_in_config
    if resource_id_resolved is None:
        raise ValueError("resource_id is missing")
    constraints.valid_resource_id(resource_id_resolved)
    name_in_config: str = config.pop("resource_name", None)
    resource_name: str = name or name_in_config or resource_id  # type: ignore [assignment]

    resource = Resource(
        id=id or unique_id.make_unique_id(),
        resource_id=resource_id_resolved,
        name=resource_name,
        config=config,
        entry_repo_id=entry_repo_id,
        message=message or "Resource added.",
        op=ResourceOp.ADDED,
        version=1,
        last_modified=created_at or timings.utc_now(),
        last_modified_by=user or created_by or "unknown",
    )
    event = events.ResourceCreated(
        id=resource.id,
        resourceId=resource.resource_id,
        entryRepoId=resource.entry_repository_id,
        name=resource.name,
        config=resource.config,
        timestamp=resource.last_modified,
        user=resource.last_modified_by,
        message=resource.message,
    )
    return resource, [event]


# ===== Repository =====
