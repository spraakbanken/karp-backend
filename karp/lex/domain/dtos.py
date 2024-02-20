"""DTOs for entries and resources."""

import typing

import pydantic

from karp.foundation import alias_generators
from karp.foundation.value_objects import unique_id
from karp.lex.domain.entities.entry import EntryOp


class BaseModel(pydantic.BaseModel):
    class Config:
        # arbitrary_types_allowed = True
        # extra = "forbid"
        alias_generator = alias_generators.to_lower_camel


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


class ResourceDto(EntityDto):
    resource_id: str
    is_published: bool
    name: str
    config: dict
