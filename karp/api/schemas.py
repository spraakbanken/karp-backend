import typing  # noqa: D100, I001
from enum import Enum
from typing import Dict, Optional

import pydantic
import ulid

from karp.lex_core import alias_generators
from karp.lex_core.value_objects import unique_id


class BaseModel(pydantic.BaseModel):
    """Base class for schema classes."""

    class Config:  # noqa: D106
        alias_generator = alias_generators.to_lower_camel
        json_encoders: typing.ClassVar = {ulid.ULID: lambda u: u.str}

    def serialize(self) -> dict:
        """Serialize model to dict."""
        return self.dict(by_alias=True)


class PermissionLevel(str, Enum):  # noqa: D101
    write = "write"
    read = "read"
    admin = "admin"


class Entry(BaseModel):  # noqa: D101
    entry_id: str
    resource: str
    version: int
    entry: typing.Dict
    last_modified_by: str
    last_modified: float


class EntryBase(BaseModel):  # noqa: D101
    entry: Dict


class EntryAdd(EntryBase):  # noqa: D101
    message: str = ""


class EntryUpdate(EntryBase):  # noqa: D101
    message: str
    version: int


class EntryAddResponse(BaseModel):  # noqa: D101
    newID: unique_id.UniqueIdStr


class ResourceBase(BaseModel):  # noqa: D101
    resource_id: str
    name: str
    config: typing.Dict
    message: Optional[str] = None


class ResourcePublic(ResourceBase):  # noqa: D101
    id: unique_id.UniqueIdStr  # noqa: A003
    last_modified: float
    is_published: Optional[bool] = None
    version: Optional[int] = None


class ResourceProtected(ResourcePublic):  # noqa: D101
    last_modified_by: str
    is_published: Optional[bool] = None
    version: Optional[int] = None