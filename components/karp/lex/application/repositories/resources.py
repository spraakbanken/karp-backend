import abc
import logging
import typing
import uuid
from typing import Dict, List, Optional, Tuple, Union

from karp.foundation import events, repository, unit_of_work
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

    def get_by_resource_id(
        self, resource_id: str, *, version: Optional[int] = None
    ) -> entities.Resource:
        resource = self.get_by_resource_id_optional(resource_id, version=version)

        if not resource:
            raise self.EntityNotFound(
                f"Entity with resource_id='{resource_id}' can't be found."
            )

        return resource

    def get_by_resource_id_optional(
        self, resource_id: str, *, version: Optional[int] = None
    ) -> typing.Optional[entities.Resource]:
        resource = self._by_resource_id(resource_id)
        if not resource:
            return None

        if version:
            resource = self._by_id(resource.entity_id, version=version)
        if resource:
            self.seen.add(resource)
        return resource

    by_resource_id = get_by_resource_id

    @abc.abstractmethod
    def _by_resource_id(
        self,
        resource_id: str,
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


class ResourceUnitOfWork(unit_of_work.UnitOfWork[ResourceRepository]):
    def __init__(self, event_bus: events.EventBus):
        unit_of_work.UnitOfWork.__init__(self, event_bus=event_bus)

    @property
    def resources(self) -> ResourceRepository:
        return self.repo
