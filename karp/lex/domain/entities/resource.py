"""LexicalResource"""
import abc
import enum
import typing
from typing import Any, Callable, Dict, List, Optional, Type, Union
from uuid import UUID

from karp.domain import constraints
from karp.domain.errors import ConfigurationError
from karp.domain.models import event_handler
from karp.foundation.entity import Entity, TimestampedVersionedEntity
from karp.foundation.value_objects import PermissionLevel
from .entry import Entry, create_entry
from karp.domain.models.events import DomainEvent
from karp.lex.domain import errors, events
from karp.foundation.value_objects import unique_id
from karp.utility import json_schema, time
from karp.utility.container import create_field_getter
from karp.utility.time import utc_now

# pylint: disable=unsubscriptable-object


class ResourceOp(enum.Enum):
    ADDED = "ADDED"
    UPDATED = "UPDATED"
    DELETED = "DELETED"


class Resource(TimestampedVersionedEntity):
    DiscardedEntityError = errors.DiscardedEntityError
    resource_type: str = "resource"

    @classmethod
    def create_resource(cls, resource_type: str, resource_config: Dict):
        if resource_type == cls.resource_type:
            return cls.from_dict(resource_config)

    @classmethod
    def from_dict(cls, config: Dict, **kwargs):

        resource_id = config.pop("resource_id")
        resource_name = config.pop("resource_name")

        #     entry_repository = EntryRepository.create(
        #         config["entry_repository_type"],
        #         entry_repository_settings
        #     )

        resource = cls(
            resource_id=resource_id,
            name=resource_name,
            config=config,
            message="Resource added.",
            op=ResourceOp.ADDED,
            entity_id=unique_id.make_unique_id(),
            version=1,
            **kwargs,
        )
        resource.queue_event(
            events.ResourceCreated(
                id=resource.id,
                resource_id=resource.resource_id,
                name=resource.name,
                config=resource.config,
                timestamp=resource.last_modified,
                user=resource.last_modified_by,
                message=resource.message,
            )
        )
        return resource

    class NewReleaseAdded(DomainEvent):
        def mutate(self, obj):
            obj._validate_event_applicability(self)
            release = Release(
                entity_id=self.release_id,
                name=self.release_name,
                publication_date=self.timestamp,
                description=self.release_description,
                aggregate_root=obj,
            )
            obj._releases.append(release)
            obj._last_modified = self.timestamp
            obj._last_modified_by = self.user
            obj._message = f"Release '{self.release_name}' created."
            obj._increment_version()

    def __init__(
        self,
        *,
        entity_id: unique_id.UniqueId,
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
        **kwargs,
    ):
        super().__init__(entity_id=entity_id, version=version, **kwargs)
        self._resource_id = resource_id
        self._name = name
        self.is_published = is_published
        self.config = config
        self._message = message
        self._op = op
        self._releases = []
        # self._entry_repository = None
        # self.entry_repository_type = entry_repository_type
        # self.entry_repository_settings = entry_repository_settings
        self._entry_json_schema = None
        self._entry_repo_id = entry_repo_id
        # if not self.events or not isinstance(self.events[-1], events.ResourceCreated):
        #     self.queue_event(
        #         events.ResourceLoaded(
        #             id=self._id,
        #             resource_id=self._resource_id,
        #             name=self._name,
        #             config=self.config,
        #             timestamp=self._last_modified,
        #             user=self._last_modified_by,
        #             message=self._message,
        #             version=self.version,
        #         )
        #     )

    @property
    def resource_id(self) -> str:
        return self._resource_id

    @property
    def entry_repository_id(self) -> unique_id.UniqueId:
        return self._entry_repo_id

    @property
    def entry_repository_settings(self) -> typing.Dict:
        return self.config["entry_repository_settings"]

    @entry_repository_settings.setter
    def entry_repository_settings(self, entry_repository_settings: typing.Dict):
        self.config["entry_repository_settings"] = entry_repository_settings

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._check_not_discarded()
        self._name = name

    @property
    def message(self):
        return self._message

    @property
    def releases(self):
        """Releases for this resource."""
        return self._releases

    @property
    def op(self):
        return self._op

    # @property
    # def entry_repository(self):
    #     from karp.domain.repository import EntryRepository

    #     if self._entry_repository is None:
    #         self._entry_repository = EntryRepository.create(
    #             self.entry_repository_type,
    #             {"table_name": self._resource_id, "config": self.config},
    #         )
    #     return self._entry_repository

    def stamp(
        self,
        *,
        user: str,
        timestamp: float = None,
        message: str = None,
        increment_version: bool = True,
    ):
        self._extracted_from_publish_9(timestamp, user, message, "Updated")
        if increment_version:
            self._version += 1
        self.queue_event(
            events.ResourceUpdated(
                entity_id=self.id,
                resource_id=self.resource_id,
                name=self.name,
                config=self.config,
                version=self.version,
                timestamp=self.last_modified,
                user=self.last_modified_by,
                message=self.message,
                entry_repo_id=self.entry_repository_id,
            )
        )

    def publish(
        self,
        *,
        user: str,
        message: str,
        timestamp: float = None,
    ):
        self._extracted_from_publish_9(timestamp, user, message, "Published")
        self._version += 1
        self.is_published = True
        self.queue_event(
            events.ResourcePublished(
                entity_id=self.id,
                resource_id=self.resource_id,
                entry_repo_id=self.entry_repository_id,
                timestamp=self.last_modified,
                user=self.last_modified_by,
                version=self.version,
                name=self.name,
                config=self.config,
                message=self.message,
            )
        )

    def _extracted_from_publish_9(self, timestamp, user, message, arg3):
        self._check_not_discarded()
        self._last_modified = timestamp or utc_now()
        self._last_modified_by = user
        self._message = message or arg3
        self._op = ResourceOp.UPDATED

    def add_new_release(self, *, name: str, user: str, description: str):
        self._check_not_discarded()
        event = Resource.NewReleaseAdded(
            entity_id=self.id,
            entity_version=self.version,
            entity_last_modified=self.last_modified,
            release_id=unique_id.make_unique_id(),
            release_name=constraints.length_gt_zero("name", name),
            user=user,
            release_description=description,
        )
        event.mutate(self)
        event_handler.publish(event)

        return self.release_with_name(name)

    def release_with_name(self, name: str):
        self._check_not_discarded()
        pass

    def discard(self, *, user: str, message: str, timestamp: float = None):
        self._check_not_discarded()
        self._op = ResourceOp.DELETED
        self._message = message or "Entry deleted."
        self._discarded = True
        self._last_modified_by = user
        self._last_modified = timestamp or utc_now()
        self._version += 1
        self.queue_event(
            events.ResourceDiscarded(
                entity_id=self.id,
                version=self.version,
                entry_repo_id=self.entry_repository_id,
                timestamp=self.last_modified,
                user=self.last_modified_by,
                message=self.message,
                resource_id=self.resource_id,
                name=self.name,
                config=self.config,
            )
        )

    @property
    def entry_json_schema(self) -> Dict:
        if self._entry_json_schema is None:
            self._entry_json_schema = json_schema.create_entry_json_schema(
                self.config["fields"]
            )
        return self._entry_json_schema

    # @property
    def id_getter(self) -> Callable[[Dict], str]:
        return create_field_getter(self.config["id"], str)

    def create_entry_from_dict(
        self,
        entry_raw: Dict,
        *,
        user: str,
        entity_id: unique_id.UniqueId,
        message: Optional[str] = None,
    ) -> Entry:
        self._check_not_discarded()
        id_getter = self.id_getter()
        return create_entry(
            id_getter(entry_raw),
            entry_raw,
            repo_id=self.entry_repository_id,
            # resource_id=self.resource_id,
            last_modified_by=user,
            message=message,
            entity_id=entity_id,
        )

    def is_protected(self, level: PermissionLevel):
        """
        Level can be READ, WRITE or ADMIN
        """
        protection = self.config.get("protected", {})
        return level == "WRITE" or level == "ADMIN" or protection.get("read")


# ===== Entities =====
class Release(Entity):
    def __init__(self, name: str, publication_date: float, description: str, **kwargs):
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


def create_resource(
    config: Dict,
    created_by: str,
    entry_repo_id: unique_id.UniqueId,
    created_at: float = None,
    entity_id: unique_id.UniqueId = None,
    resource_id: typing.Optional[str] = None,
    message: typing.Optional[str] = None,
    name: typing.Optional[str] = None,
) -> Resource:

    resource_id_in_config = config.pop("resource_id", None)
    resource_id = resource_id or resource_id_in_config
    if not resource_id:
        raise ValueError("resource_id is missing")
    if not constraints.valid_resource_id(resource_id):
        raise ValueError(f"resource_id is not valid: value='{resource_id}")
    name_in_config = config.pop("resource_name", None)
    resource_name = name or name_in_config or resource_id
    entity_id = entity_id or unique_id.make_unique_id()
    #
    #     entry_repository = EntryRepository.create(
    #         config["entry_repository_type"],
    #         entry_repository_settings
    #     )

    resource = Resource(
        entity_id=entity_id,
        resource_id=resource_id,
        name=resource_name,
        config=config,
        entry_repo_id=entry_repo_id,
        message=message or "Resource added.",
        op=ResourceOp.ADDED,
        version=1,
        last_modified=created_at or time.utc_now(),
        last_modified_by=created_by,
    )
    resource.queue_event(
        events.ResourceCreated(
            entity_id=resource.id,
            resource_id=resource.resource_id,
            entry_repo_id=resource.entry_repository_id,
            name=resource.name,
            config=resource.config,
            timestamp=resource.last_modified,
            user=resource.last_modified_by,
            message=resource.message,
        )
    )
    return resource


# ===== Repository =====