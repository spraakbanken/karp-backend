import enum
import typing

import pydantic


class Scope(str, enum.Enum):  # noqa: D101
    admin = "ADMIN"
    write = "WRITE"
    read = "READ"


class ResourcePermissionDto(pydantic.BaseModel):  # noqa: D101
    resource_id: str
    protected: typing.Optional[Scope]
