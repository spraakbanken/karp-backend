from typing import Iterable, Optional

from injector import inject

from karp import plugins
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

    def _from_resource(self, resource: Resource, expand_plugins=True) -> ResourceDto:
        return plugins.transform_resource(
            self._plugins, ResourceDto.from_resource(resource), expand_plugins=expand_plugins
        )

    def by_resource_id(self, resource_id: str, version: Optional[int] = None, **kwargs) -> ResourceDto:
        result = self._resources.by_resource_id(resource_id, version=version)
        return self._from_resource(result, **kwargs)

    def by_resource_id_optional(
        self, resource_id: str, version: Optional[int] = None, **kwargs
    ) -> Optional[ResourceDto]:
        result = self._resources.by_resource_id_optional(resource_id, version=version)
        if result is not None:
            return self._from_resource(result, **kwargs)

    def get_published_resources(self, **kwargs) -> Iterable[ResourceDto]:
        return [self._from_resource(r, **kwargs) for r in self._resources.get_published_resources()]

    def get_all_resources(self, **kwargs) -> Iterable[ResourceDto]:
        return [self._from_resource(r, **kwargs) for r in self._resources.get_all_resources()]
