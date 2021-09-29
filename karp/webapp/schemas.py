import typing
from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel


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
