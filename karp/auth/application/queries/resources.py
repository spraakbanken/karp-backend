import abc
import typing

import pydantic


class ResourcePermissionDto(pydantic.BaseModel):
    pass


class GetResourcePermissions(abc.ABC):
    @abc.abstractmethod
    def query(self) -> typing.List[ResourcePermissionDto]:
        pass
