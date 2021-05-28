import abc
from typing import Optional, Union
import uuid

from . import errors, model


class Repository(abc.ABC):
    def __init__(self):
        self.seen = set()

    def put(self, entity):
        self._put(entity)
        self.seen.add(entity)

    @abc.abstractmethod
    def _put(self, entity):
        raise NotImplementedError()

    def by_id(
        self, id: Union[uuid.UUID, str], *, version: Optional[int] = None
    ) -> Optional[model.Entity]:
        entity = self._by_id(id, version=version)
        if entity:
            self.seen.add(entity)
        return entity

    @abc.abstractmethod
    def _by_id(
        self, id: Union[uuid.UUID, str], *, version: Optional[int] = None
    ) -> Optional[model.Entity]:
        raise NotImplementedError()


class ResourceRepository(Repository):
    @abc.abstractmethod
    def check_status(self):
        raise errors.RepositoryStatusError()

    # @abc.abstractmethod
    # def resource_ids(self) -> List[Resource]:
    #     raise NotImplementedError()

    def by_resource_id(
        self, resource_id: str, *, version: Optional[int] = None
    ) -> Optional[model.Resource]:
        resource = self._by_resource_id(resource_id, version=version)
        if resource:
            self.seen.add(resource)
        return resource

    @abc.abstractmethod
    def _by_resource_id(
        self, resource_id: str, *, version: Optional[int] = None
    ) -> Optional[model.Resource]:
        raise NotImplementedError()

    # @abc.abstractmethod
    # def resources_with_id(self, resource_id: str):
    #     raise NotImplementedError()

    # @abc.abstractmethod
    # def resource_with_id_and_version(self, resource_id: str, version: int):
    #     raise NotImplementedError()

    # @abc.abstractmethod
    # def get_active_resource(self, resource_id: str) -> Optional[Resource]:
    #     raise NotImplementedError()

    # @abc.abstractmethod
    # def get_published_resources(self) -> List[Resource]:
    #     raise NotImplementedError()
