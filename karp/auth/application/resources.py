import enum
import typing

import pydantic


class Scope(str, enum.Enum):
    admin = "ADMIN"
    write = "WRITE"
    read = "READ"


class ResourcePermissionDto(pydantic.BaseModel):
    resource_id: str
    protected: typing.Optional[Scope]
