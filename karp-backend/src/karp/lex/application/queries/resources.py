import abc  # noqa: D100, I001
from typing import Iterable, Optional, Dict

import pydantic

from karp.foundation.value_objects import UniqueIdStr, UniqueId
from karp.foundation.value_objects.unique_id import UniqueIdPrimitive


class ResourceDto(pydantic.BaseModel):  # noqa: D101
    resource_id: str
    entity_id: UniqueIdStr
    is_published: bool
    version: int
    name: str
    last_modified_by: str
    message: str
    last_modified: float
    config: Dict
    entry_repository_id: UniqueIdStr
    discarded: bool


class GetPublishedResources(abc.ABC):  # noqa: D101
    @abc.abstractmethod
    def query(self) -> Iterable[ResourceDto]:  # noqa: D102
        pass


class GetResources(abc.ABC):  # noqa: D101
    @abc.abstractmethod
    def query(self) -> Iterable[ResourceDto]:  # noqa: D102
        pass


class GetEntryRepositoryId(abc.ABC):  # noqa: D101
    @abc.abstractmethod
    def query(self, resource_id: str) -> UniqueId:  # noqa: D102
        raise NotImplementedError()


class ReadOnlyResourceRepository(abc.ABC):  # noqa: D101
    def get_by_resource_id(  # noqa: D102
        self, resource_id: str, version: Optional[int] = None
    ) -> Optional[ResourceDto]:
        resource = self._get_by_resource_id(resource_id)
        if not resource:
            return None

        if version is not None:
            resource = self.get_by_id(resource.entity_id, version=version)
        return resource

    @abc.abstractmethod
    def get_by_id(  # noqa: D102
        self, entity_id: UniqueIdPrimitive, version: Optional[int] = None
    ) -> Optional[ResourceDto]:
        pass

    @abc.abstractmethod
    def _get_by_resource_id(self, resource_id: str) -> Optional[ResourceDto]:
        pass

    @abc.abstractmethod
    def get_published_resources(self) -> Iterable[ResourceDto]:  # noqa: D102
        pass
