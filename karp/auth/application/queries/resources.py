import abc  # noqa: D100, I001
import enum
import typing

import pydantic

from karp.foundation.value_objects.permission_level import PermissionLevel


class Scope(str, enum.Enum):  # noqa: D101
    admin = "ADMIN"
    write = "WRITE"
    read = "READ"


class ResourcePermissionDto(pydantic.BaseModel):  # noqa: D101
    resource_id: str
    protected: typing.Optional[Scope]
