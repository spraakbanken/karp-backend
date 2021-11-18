import abc
import enum
import typing

import pydantic


class Scope(str, enum.Enum):
    admin = 'ADMIN'
    write = 'WRITE'
    read = 'READ'


class ResourcePermissionDto(pydantic.BaseModel):
    resource_id: str
    protected: typing.Optional[Scope]


class GetResourcePermissions(abc.ABC):
    @abc.abstractmethod
    def query(self) -> typing.List[ResourcePermissionDto]:
        pass
