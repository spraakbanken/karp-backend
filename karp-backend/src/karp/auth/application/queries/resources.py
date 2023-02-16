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


class GetResourcePermissions(abc.ABC):  # noqa: D101
    @abc.abstractmethod
    def query(self) -> typing.List[ResourcePermissionDto]:  # noqa: D102
        pass


class IsResourceProtected(abc.ABC):  # noqa: D101
    @abc.abstractmethod
    def query(self, resource_id: str, level: PermissionLevel) -> bool:  # noqa: D102
        return True
