from enum import Enum
from typing import Optional, Dict
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


class Entry(BaseModel):
    entry_id: str


class EntryBase(BaseModel):
    entry: Dict


class EntryAdd(EntryBase):
    message: str = ""


class EntryUpdate(EntryBase):
    message: str
    version: int
