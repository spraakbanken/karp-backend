from datetime import datetime
from typing import Generic, Optional, TypeVar

from karp.lex_core import alias_generators
from karp.lex_core.value_objects import UniqueIdStr
from pydantic import root_validator
from pydantic.generics import GenericModel

T = TypeVar("T")


class GenericEntryDto(GenericModel, Generic[T]):
    entry: T
    last_modified_by: Optional[str]
    last_modified: Optional[datetime]
    entity_id: Optional[UniqueIdStr]
    message: Optional[str]
    version: Optional[int]
    resource: Optional[str]
    discarded: bool = False

    class Config:
        extra = "forbid"
        alias_generator = alias_generators.to_lower_camel

    @root_validator(pre=True)
    @classmethod
    def allow_snake_case(cls, values):
        if "last_modified" in values:
            values["lastModified"] = values.pop("last_modified")
        if "last_modified_by" in values:
            values["lastModifiedBy"] = values.pop("last_modified_by")
        if "entity_id" in values:
            values["entityId"] = values.pop("entity_id")
        return values

    def serialize(self):
        return self.dict(by_alias=True, exclude_none=True)


class EntryDto(GenericEntryDto[dict]):
    ...
