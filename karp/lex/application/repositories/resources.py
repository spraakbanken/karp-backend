import abc  # noqa: D100, I001
import logging
import typing
import uuid  # noqa: F401
from typing import Dict, List, Optional, Tuple, Union  # noqa: F401

from karp.foundation import repository
from karp.lex.domain import entities

from karp.lex.domain import errors

logger = logging.getLogger("karp")


class ResourceRepository(repository.Repository):  # noqa: D101
    EntityNotFound = errors.ResourceNotFound

    @abc.abstractmethod
    def resource_ids(self) -> typing.Iterable[str]:  # noqa: D102
        raise NotImplementedError()

    def by_resource_id(  # noqa: D102
        self, resource_id: str, *, version: Optional[int] = None
    ) -> entities.Resource:
        if resource := self.by_resource_id_optional(resource_id, version=version):
            return resource
        else:
            raise self.EntityNotFound(f"Entity with resource_id='{resource_id}' can't be found.")

    def by_resource_id_optional(  # noqa: D102
        self, resource_id: str, *, version: Optional[int] = None
    ) -> typing.Optional[entities.Resource]:
        resource = self._by_resource_id(resource_id)
        if not resource:
            return None

        if version:
            resource = self._by_id(resource.entity_id, version=version)
        return resource

    @abc.abstractmethod
    def _by_resource_id(
        self,
        resource_id: str,
    ) -> Optional[entities.Resource]:
        raise NotImplementedError()

    def get_published_resources(self) -> typing.List[entities.Resource]:  # noqa: D102
        return list(self._get_published_resources())

    @abc.abstractmethod
    def _get_published_resources(self) -> typing.Iterable[entities.Resource]:
        raise NotImplementedError()

    def get_all_resources(self) -> typing.List[entities.Resource]:  # noqa: D102
        return list(self._get_all_resources())

    @abc.abstractmethod
    def _get_all_resources(self) -> typing.Iterable[entities.Resource]:
        raise NotImplementedError()
