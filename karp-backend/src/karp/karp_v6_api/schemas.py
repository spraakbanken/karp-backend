import typing  # noqa: D100, I001
from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel

from karp.foundation.value_objects import unique_id


class SystemResponse(BaseModel):  # noqa: D101
    message: str = "ok"

    def __bool__(self):  # noqa: ANN204, D105
        return True


class SystemOk(SystemResponse):  # noqa: D101
    pass


class SystemNotOk(SystemResponse):  # noqa: D101
    def __bool__(self):  # noqa: ANN204, D105
        return False


class SystemMonitorResponse(BaseModel):  # noqa: D101
    database: str


class PermissionLevel(str, Enum):  # noqa: D101
    write = "write"
    read = "read"
    admin = "admin"


class EntryFormat(str, Enum):  # noqa: D101
    json = "json"
    csv = "csv"
    xml = "xml"
    lmf = "lmf?"
    tsb = "tsb"


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


class EntityIdMixin(BaseModel):  # noqa: D101
    entity_id: unique_id.UniqueIdStr


class EntryAddResponse(BaseModel):  # noqa: D101
    newID: unique_id.UniqueIdStr


class ResourceBase(BaseModel):  # noqa: D101
    resource_id: str
    name: str
    config: typing.Dict
    message: Optional[str] = None
    entry_repo_id: Optional[unique_id.UniqueIdStr] = None
    is_published: Optional[bool] = None
    version: Optional[int] = None


class ResourceCreate(ResourceBase):  # noqa: D101
    pass


class ResourcePublic(EntityIdMixin, ResourceBase):  # noqa: D101
    last_modified: float


class ResourceProtected(ResourcePublic):  # noqa: D101
    last_modified_by: str


class ResourcePublish(BaseModel):  # noqa: D101
    message: str
    version: int
    resource_id: Optional[str]
