import typing
from enum import Enum
from typing import Dict, Optional, Union

import pydantic
import ulid

from karp.foundation import alias_generators
from karp.foundation.value_objects import unique_id
from karp.lex import EntryDto


class BaseModel(pydantic.BaseModel):
    """Base class for schema classes."""

    model_config = {"alias_generator": alias_generators.to_lower_camel, "populate_by_name": True}


class EntryAdd(BaseModel):
    entry: Dict
    message: str = ""


class EntryUpdate(EntryAdd):
    message: str
    version: int


class EntryAddResponse(BaseModel):
    newID: unique_id.UniqueIdStr


class ResourcePublic(BaseModel):
    id: unique_id.UniqueIdStr
    resource_id: str
    name: str
    config: typing.Dict
    message: Optional[str] = None
    last_modified: float
    is_published: Optional[bool] = None
    version: Optional[int] = None


class ResourceProtected(ResourcePublic):
    last_modified_by: str


class QueryResponse(pydantic.BaseModel):
    total: int
    hits: list[Union[EntryDto, object]]
    distribution: Optional[Dict[str, int]]


class QueryStatsResponse(pydantic.BaseModel):
    total: int
    distribution: Dict[str, int]


class EntriesByIdResponse(pydantic.BaseModel):
    total: int
    hits: list[Union[EntryDto, object]]
