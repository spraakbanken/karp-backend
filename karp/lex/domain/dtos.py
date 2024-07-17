"""DTOs for entries and resources."""

import typing

import pydantic

from karp.foundation import alias_generators
from karp.foundation.value_objects import unique_id
from karp.lex.domain.entities import Entry, Resource
from karp.lex.domain.entities.entry import EntryOp
from karp.lex.domain.value_objects import ResourceConfig


class BaseModel(pydantic.BaseModel):
    model_config = {
        # arbitrary_types_allowed = True
        # extra = "forbid"
        "alias_generator": alias_generators.to_lower_camel
    }


class IdMixin(BaseModel):
    id: unique_id.UniqueIdStr


class EntityDto(IdMixin, BaseModel):
    version: int
    last_modified: float
    last_modified_by: str
    message: str | None = None
    discarded: bool = False


class EntryDto(EntityDto):
    resource: str
    entry: typing.Dict

    @classmethod
    def from_entry(cls, entry: Entry) -> "EntryDto":
        return EntryDto(
            id=entry.id,
            resource=entry.resource_id,
            version=entry.version,
            entry=entry.body,
            lastModified=entry.last_modified,
            lastModifiedBy=entry.last_modified_by,
            message=entry.message,
        )


class ResourceDto(EntityDto):
    resource_id: str
    is_published: bool
    name: str
    config: ResourceConfig

    @classmethod
    def from_resource(cls, resource: Resource) -> "ResourceDto":
        return ResourceDto(
            id=resource.id,
            resourceId=resource.resource_id,
            version=resource.version,
            config=resource.config,
            isPublished=resource.is_published,
            lastModified=resource.last_modified,
            lastModifiedBy=resource.last_modified_by,
            message=resource.message,
            name=resource.name,
            discarded=resource.discarded,
        )
