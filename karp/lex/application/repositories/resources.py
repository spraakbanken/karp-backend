import abc
import logging
import typing
import uuid
from typing import Dict, List, Optional, Tuple, Union

from karp.foundation import repository
from karp.lex.domain import entities

from karp.lex.domain import errors

logger = logging.getLogger("karp")


class ResourceRepository(repository.Repository[entities.Resource]):
    EntityNotFound = errors.ResourceNotFound

    @abc.abstractmethod
    def check_status(self):
        pass

    @abc.abstractmethod
    def resource_ids(self) -> typing.Iterable[str]:
        raise NotImplementedError()

    def by_resource_id(
        self, resource_id: str, *, version: Optional[int] = None
    ) -> entities.Resource:
        resource = self._by_resource_id(resource_id, version=version)
        if resource:
            self.seen.add(resource)
        else:
            raise self.EntityNotFound(
                f"Entity with resource_id='{resource_id}' can't be found.")
        return resource

    @abc.abstractmethod
    def _by_resource_id(
        self, resource_id: str, *, version: Optional[int] = None
    ) -> Optional[entities.Resource]:
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

    def get_published_resources(self) -> typing.List[entities.Resource]:
        published_resources = []
        for resource in self._get_published_resources():
            self.seen.add(resource)
            published_resources.append(resource)
        return published_resources

    @abc.abstractmethod
    def _get_published_resources(self) -> typing.Iterable[entities.Resource]:
        raise NotImplementedError()

    def get_all_resources(self) -> typing.List[entities.Resource]:
        all_resources = []
        for resource in self._get_all_resources():
            self.seen.add(resource)
            all_resources.append(resource)
        return all_resources

    @abc.abstractmethod
    def _get_all_resources(self) -> typing.Iterable[entities.Resource]:
        raise NotImplementedError()
