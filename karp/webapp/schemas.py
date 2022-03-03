import typing
from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel

from karp.foundation.value_objects import unique_id


class SystemResponse(BaseModel):
    message: str = "ok"

    def __bool__(self):
        return True


class SystemOk(SystemResponse):
    pass


class SystemNotOk(SystemResponse):
    def __bool__(self):
        return False


class SystemMonitorResponse(BaseModel):
    database: str


class PermissionLevel(str, Enum):
    write = "write"
    read = "read"
    admin = "admin"


class EntryFormat(str, Enum):
    json = "json"
    csv = "csv"
    xml = "xml"
    lmf = "lmf?"
    tsb = "tsb"


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


class EntityIdMixin(BaseModel):
    entity_id: unique_id.UniqueId


class ResourceBase(BaseModel):
    resource_id: str
    name: str
    config: typing.Dict
    message: Optional[str] = None
    entry_repo_id: Optional[unique_id.UniqueId]


class ResourceCreate(ResourceBase):
    pass


class ResourcePublic(EntityIdMixin, ResourceBase):
    last_modified: float
    last_modified_by: str


class ResourcePublish(BaseModel):
    message: str
    resource_id: Optional[str]
