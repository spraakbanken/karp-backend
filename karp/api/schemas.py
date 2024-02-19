import typing
from enum import Enum
from typing import Dict, Optional

import pydantic
import ulid

from karp.foundation import alias_generators
from karp.foundation.value_objects import unique_id


class BaseModel(pydantic.BaseModel):
    """Base class for schema classes."""

    class Config:
        alias_generator = alias_generators.to_lower_camel
        json_encoders: typing.ClassVar = {ulid.ULID: lambda u: u.str}

    def serialize(self) -> dict:
        """Serialize model to dict."""
        return self.dict(by_alias=True)


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
