from typing import Iterable, Optional  # noqa: I001

import sqlalchemy as sa
from sqlalchemy import sql

from karp.lex.application.dtos import ResourceDto
from karp.lex_core.value_objects.unique_id import UniqueId

from karp.lex_infrastructure.sql.sql_models import ResourceModel
from karp.lex.application.repositories import ResourceRepository
from karp.lex.domain.entities import Resource


class ResourceQueries:
    """Implements various queries about the resource list, giving answers as DTO.
    Used for example in resources_api.py.

    For now the API is a subset of ResourceRepository, but returning DTOs."""

    def __init__(self, resources: ResourceRepository):
        self._resources = resources

    def by_resource_id_optional(
        self, resource_id: str, version: Optional[int] = None
    ) -> Optional[ResourceDto]:
        result = self._resources.by_resource_id_optional(resource_id, version=version)
        if result is not None:
            return resource_to_dto(result)

    def by_id_optional(
        self, entity_id: UniqueId, version: Optional[int] = None
    ) -> Optional[ResourceDto]:
        result = self._resources.by_id_optional(entity_id, version=version)
        if result is not None:
            return resource_to_dto(result)

    def get_published_resources(self) -> Iterable[ResourceDto]:
        return map(resource_to_dto, self._resources.get_published_resources())

    def get_all_resources(self) -> Iterable[ResourceDto]:
        return map(resource_to_dto, self._resources.get_all_resources())


def resource_to_dto(resource: Resource) -> ResourceDto:
    return ResourceDto(
        id=resource.id,
        resourceId=resource.resource_id,
        version=resource.version,
        config=resource.config,
        isPublished=resource.is_published,
        lastModified=resource.last_modified,
        lastModifiedBy=resource.last_modified_by,
        message=resource.message,
        name=resource.name,
        discarded=resource.discarded,
    )
