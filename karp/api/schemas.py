from typing import Dict, Optional, Union

import pydantic

from karp.foundation import alias_generators
from karp.foundation.value_objects import unique_id
from karp.lex import EntryDto
from karp.lex.domain.value_objects import ResourceConfig


class BaseModel(pydantic.BaseModel):
    """Base class for schema classes."""

    model_config = {"alias_generator": alias_generators.to_lower_camel, "populate_by_name": True}


class EntryAdd(BaseModel):
    entry: Dict
    message: str = ""


class EntryUpdate(EntryAdd):
    message: str
    version: int


class EntryPreview(BaseModel):
    entry: Dict


class EntryAddResponse(BaseModel):
    newID: unique_id.UniqueIdStr


class EntryPreviewResponse(BaseModel):
    entry: Dict


class ResourcePublic(BaseModel):
    id: unique_id.UniqueIdStr
    resource_id: str
    name: str
    config: ResourceConfig
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
