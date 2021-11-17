import abc
from typing import Iterable

import pydantic

from karp.foundation.value_objects import UniqueId


class ResourceDto(pydantic.BaseModel):
    resource_id: str
    id: UniqueId
    is_published: bool
    version: int
    last_modified: float


class GetPublishedResources(abc.ABC):
    @abc.abstractmethod
    def query(self) -> Iterable[ResourceDto]:
        pass


class GetResources(abc.ABC):
    @abc.abstractmethod
    def query(self) -> Iterable[ResourceDto]:
        pass


class GetEntryRepositoryId(abc.ABC):
    @abc.abstractmethod
    def query(self, resource_id: str) -> UniqueId:
        raise NotImplementedError()
