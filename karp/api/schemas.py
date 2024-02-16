import typing
from enum import Enum
from typing import Dict, Optional

import pydantic
import ulid

from karp.lex_core import alias_generators
from karp.lex_core.value_objects import unique_id


class BaseModel(pydantic.BaseModel):
    """Base class for schema classes."""

    class Config:
        alias_generator = alias_generators.to_lower_camel
        json_encoders: typing.ClassVar = {ulid.ULID: lambda u: u.str}

    def serialize(self) -> dict:
        """Serialize model to dict."""
        return self.dict(by_alias=True)


class PermissionLevel(str, Enum):
    write = "write"
    read = "read"
    admin = "admin"


class Entry(BaseModel):
    entry_id: str
    resource: str
    version: int
    entry: typing.Dict
    last_modified_by: str
    last_modified: float


class EntryBase(BaseModel):
    entry: Dict


class EntryAdd(EntryBase):
    message: str = ""


class EntryUpdate(EntryBase):
    message: str
    version: int


class EntryAddResponse(BaseModel):
    newID: unique_id.UniqueIdStr


class ResourceBase(BaseModel):
    resource_id: str
    name: str
    config: typing.Dict
    message: Optional[str] = None


class ResourcePublic(ResourceBase):
    id: unique_id.UniqueIdStr
    last_modified: float
    is_published: Optional[bool] = None
    version: Optional[int] = None


class ResourceProtected(ResourcePublic):
    last_modified_by: str
    is_published: Optional[bool] = None
    version: Optional[int] = None
