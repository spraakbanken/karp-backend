from typing import Iterable, Optional  # noqa: D100, I001

import sqlalchemy as sa
from sqlalchemy import sql

from karp.lex.application.dtos import ResourceDto
from karp.lex_core.value_objects.unique_id import UniqueId

from karp.lex_infrastructure.sql.sql_models import ResourceModel
from karp.lex_infrastructure.queries.base import SqlQuery
from karp.lex.application.repositories import ResourceRepository
from karp.lex.domain.entities import Resource


class SqlGetPublishedResources(SqlQuery):  # noqa: D101
    def query(self) -> Iterable[ResourceDto]:  # noqa: D102
        subq = (
            sql.select(
                ResourceModel.entity_id,
                sa.func.max(ResourceModel.last_modified).label("maxdate"),
            )
            .group_by(ResourceModel.entity_id)
            .subquery("t2")
        )

        stmt = sql.select(ResourceModel).join(
            subq,
            sa.and_(
                ResourceModel.entity_id == subq.c.entity_id,
                ResourceModel.last_modified == subq.c.maxdate,
                ResourceModel.is_published == True,  # noqa: E712
            ),
        )
        return (_row_to_dto(row) for row in self._session.connection().execute(stmt))


class SqlGetResources(SqlQuery):  # noqa: D101
    def query(self) -> Iterable[ResourceDto]:  # noqa: D102
        subq = (
            sql.select(
                ResourceModel.entity_id,
                sa.func.max(ResourceModel.last_modified).label("maxdate"),
            )
            .group_by(ResourceModel.entity_id)
            .subquery("t2")
        )

        stmt = sql.select(ResourceModel).join(
            subq,
            sa.and_(
                ResourceModel.entity_id == subq.c.entity_id,
                ResourceModel.last_modified == subq.c.maxdate,
            ),
        )
        return [_row_to_dto(row) for row in self._session.connection().execute(stmt)]


class SqlReadOnlyResourceRepository:
    def __init__(self, resources: ResourceRepository):
        self._resources = resources

    def by_resource_id_optional(  # noqa: D102
        self, resource_id: str, version: Optional[int] = None
    ) -> Optional[ResourceDto]:
        result = self._resources.by_resource_id_optional(resource_id, version=version)
        if result is not None:
            return resource_to_dto(result)

    def by_id_optional(  # noqa: D102
        self, entity_id: UniqueId, version: Optional[int] = None
    ) -> Optional[ResourceDto]:
        result = self._resources.by_id_optional(entity_id, version=version)
        if result is not None:
            return resource_to_dto(result)

    def get_published_resources(self) -> Iterable[ResourceDto]:  # noqa: D102
        return map(resource_to_dto, self._resources.get_published_resources())

    def get_all_resources(self) -> Iterable[ResourceDto]:  # noqa: D102
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


def _row_to_dto(row_proxy) -> ResourceDto:
    return ResourceDto(
        id=row_proxy.entity_id,
        resourceId=row_proxy.resource_id,
        version=row_proxy.version,
        config=row_proxy.config,
        isPublished=row_proxy.is_published,
        lastModified=row_proxy.last_modified,
        lastModifiedBy=row_proxy.last_modified_by,
        message=row_proxy.message,
        name=row_proxy.name,
        discarded=row_proxy.discarded,
    )
