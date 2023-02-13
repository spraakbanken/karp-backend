import abc
import enum
import typing

import pydantic

from karp.foundation.value_objects.permission_level import PermissionLevel


class Scope(str, enum.Enum):
    admin = "ADMIN"
    write = "WRITE"
    read = "READ"


class ResourcePermissionDto(pydantic.BaseModel):
    resource_id: str
    protected: typing.Optional[Scope]


class GetResourcePermissions(abc.ABC):
    @abc.abstractmethod
    def query(self) -> typing.List[ResourcePermissionDto]:
        pass


class IsResourceProtected(abc.ABC):
    @abc.abstractmethod
    def query(self, resource_id: str, level: PermissionLevel) -> bool:
        return True
