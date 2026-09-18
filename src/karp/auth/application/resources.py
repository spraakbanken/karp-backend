import enum
import typing

import pydantic


class Scope(str, enum.Enum):
    admin = "ADMIN"
    write = "WRITE"
    read = "READ"


class ResourcePermissionDto(pydantic.BaseModel):
    # TODO remove when v7 is removed
    resource_id: str
    protected: typing.Optional[Scope]
