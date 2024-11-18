from typing import Iterable, Optional

from injector import inject

from karp import plugins
from karp.foundation.value_objects.unique_id import UniqueId
from karp.lex.domain.dtos import ResourceDto
from karp.lex.domain.entities import Resource
from karp.lex.infrastructure.sql import ResourceRepository


class ResourceQueries:
    """Implements various queries about the resource list, giving answers as DTO.
    Used for example in resources_api.py.

    For now the API is a subset of ResourceRepository, but returning DTOs."""

    @inject
    def __init__(self, resources: ResourceRepository, plugins: plugins.Plugins):
        self._resources = resources
        self._plugins = plugins

    def _from_resource(self, resource: Resource) -> ResourceDto:
        return plugins.transform_resource(self._plugins, ResourceDto.from_resource(resource))

    def by_resource_id(self, resource_id: str, version: Optional[int] = None) -> ResourceDto:
        result = self._resources.by_resource_id(resource_id, version=version)
        return self._from_resource(result)

    def by_resource_id_optional(self, resource_id: str, version: Optional[int] = None) -> Optional[ResourceDto]:
        result = self._resources.by_resource_id_optional(resource_id, version=version)
        if result is not None:
            return self._from_resource(result)

    def by_id(self, entity_id: UniqueId, version: Optional[int] = None) -> ResourceDto:
        result = self._resources.by_id(entity_id, version=version)
        return self._from_resource(result)

    def by_id_optional(self, entity_id: UniqueId, version: Optional[int] = None) -> Optional[ResourceDto]:
        result = self._resources.by_id_optional(entity_id, version=version)
        if result is not None:
            return self._from_resource(result)

    def get_published_resources(self) -> Iterable[ResourceDto]:
        return map(self._from_resource, self._resources.get_published_resources())

    def get_all_resources(self) -> Iterable[ResourceDto]:
        return map(self._from_resource, self._resources.get_all_resources())
