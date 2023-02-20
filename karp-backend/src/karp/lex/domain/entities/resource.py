"""LexicalResource"""  # noqa: D400, D415
import enum  # noqa: I001
import typing
from typing import Any, Callable, Dict, Tuple, Optional, Type, Union  # noqa: F401

from karp.lex.domain import constraints
from karp.foundation.entity import Entity, TimestampedVersionedEntity
from karp.foundation.value_objects import PermissionLevel
from .entry import Entry, create_entry
from karp.lex.domain import errors, events
from karp.lex_core.value_objects import unique_id
from karp.utility import json_schema, time
from karp.utility.time import utc_now

# pylint: disable=unsubscriptable-object


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
        # entry_repository_type: typing.Optional[str] = None,
        # entry_repository_settings: typing.Optional[typing.Dict] = None,
        # entry_repository: EntryRepository = None,
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
        self._entry_json_schema = None
        self._entry_repo_id = unique_id.UniqueId.validate(entry_repo_id)

    @property
    def resource_id(self) -> str:  # noqa: D102
        return self._resource_id

    @property
    def entry_repository_id(self) -> unique_id.UniqueId:  # noqa: D102
        return self._entry_repo_id

    @property
    def entry_repository_settings(self) -> typing.Dict:  # noqa: D102
        return self.config["entry_repository_settings"]

    @entry_repository_settings.setter
    def entry_repository_settings(  # noqa: ANN202
        self, entry_repository_settings: typing.Dict
    ):
        self.config["entry_repository_settings"] = entry_repository_settings

    @property
    def name(self):  # noqa: ANN201, D102
        return self._name

    @name.setter
    def name(self, name):  # noqa: ANN202
        self._check_not_discarded()
        self._name = name

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
        timestamp: float = None,
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
        timestamp: Optional[float] = None,
    ):
        self._update_metadata(timestamp, user, "entry repo id updated", version=version)
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
        self._update_metadata(
            timestamp, user, message or "setting resource_id", version
        )
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
    ) -> bool:
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
    ) -> bool:
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

    def add_new_release(  # noqa: ANN201, D102
        self, *, name: str, user: str, description: str
    ):
        self._check_not_discarded()
        raise NotImplementedError()
        # event = Resource.NewReleaseAdded(
        #     id=self.id,
        #     entity_version=self.version,
        #     entity_last_modified=self.last_modified,
        #     release_id=unique_id.make_unique_id(),
        #     release_name=constraints.length_gt_zero("name", name),
        #     user=user,
        #     release_description=description,
        # )
        # event.mutate(self)

        # return self.release_with_name(name)

    def release_with_name(self, name: str):  # noqa: ANN201, D102
        self._check_not_discarded()
        raise NotImplementedError()

    def discard(  # noqa: ANN201, D102
        self, *, user: str, message: str, timestamp: float = None
    ):
        self._check_not_discarded()
        self._op = ResourceOp.DELETED
        self._message = message or "Entry deleted."
        self._discarded = True
        self._last_modified_by = user
        self._last_modified = timestamp or utc_now()
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
    def entry_json_schema(self) -> Dict:  # noqa: D102
        if self._entry_json_schema is None:
            self._entry_json_schema = json_schema.create_entry_json_schema(
                self.config["fields"]
            )
        return self._entry_json_schema

    # @property
    # def id_getter(self) -> Callable[[Dict], str]:
    #     return create_field_getter(self.config["id"], str)

    def serialize(self) -> Dict:  # noqa: D102
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

    def create_entry_from_dict(  # noqa: D102
        self,
        entry_raw: Dict,
        *,
        user: str,
        id: unique_id.UniqueId,  # noqa: A002
        message: Optional[str] = None,
        timestamp: Optional[float] = None,
    ) -> Tuple[Entry, list[events.Event]]:
        self._check_not_discarded()
        return create_entry(
            entry_raw,
            repo_id=self.entry_repository_id,
            last_modified_by=user,
            message=message,
            id=id,
            last_modified=timestamp,
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
    created_by: str = None,
    user: str = None,
    created_at: float = None,
    id: unique_id.UniqueId = None,  # noqa: A002
    resource_id: typing.Optional[str] = None,
    message: typing.Optional[str] = None,
    name: typing.Optional[str] = None,
) -> Tuple[Resource, list[events.Event]]:
    resource_id_in_config: Optional[str] = config.pop("resource_id", None)
    resource_id = resource_id or resource_id_in_config
    if resource_id is None:
        raise ValueError("resource_id is missing")
    resource_id = constraints.valid_resource_id(resource_id)
    name_in_config = config.pop("resource_name", None)
    resource_name = name or name_in_config or resource_id

    resource = Resource(
        id=id or unique_id.make_unique_id(),
        resource_id=resource_id,
        name=resource_name,
        config=config,
        entry_repo_id=entry_repo_id,
        message=message or "Resource added.",
        op=ResourceOp.ADDED,
        version=1,
        last_modified=created_at or time.utc_now(),
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
