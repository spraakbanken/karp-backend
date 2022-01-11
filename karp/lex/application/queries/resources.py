import abc
from typing import Iterable, Optional, Dict

import pydantic

from karp.foundation.value_objects import UniqueId


class ResourceDto(pydantic.BaseModel):
    resource_id: str
    id: UniqueId
    is_published: bool
    version: int
    last_modified: float
    config: Dict
    entry_repository_id: UniqueId


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


class ReadOnlyResourceRepository(abc.ABC):
    @abc.abstractmethod
    def get_by_resource_id(self, resource_id: str, version: Optional[int] = None) -> Optional[ResourceDto]:
        pass

    @abc.abstractmethod
    def get_published_resources(self) -> Iterable[ResourceDto]:
        pass
