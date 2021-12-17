from typing import Iterable, Optional

from sqlalchemy import sql

from karp.lex.application.queries import GetPublishedResources, ResourceDto, GetResources
from karp.lex.application.queries.resources import ReadOnlyResourceRepository
from karp.lex.domain.entities import resource
from karp.lex_infrastructure.sql.sql_models import ResourceModel
from karp.lex_infrastructure.queries.base import SqlQuery


class SqlGetPublishedResources(
    GetPublishedResources,
    SqlQuery
):
    def query(self) -> Iterable[ResourceDto]:
        stmt = sql.select(ResourceModel).where(
            ResourceModel.is_published == True)
        return (
            _row_to_dto(row)
            for row in self._conn.execute(stmt)
        )


class SqlGetResources(
    GetResources,
    SqlQuery
):
    def query(self) -> Iterable[ResourceDto]:
        stmt = sql.select(ResourceModel)
        return (
            _row_to_dto(row)
            for row in self._conn.execute(stmt)
        )


class SqlReadOnlyResourceRepository(
    ReadOnlyResourceRepository,
    SqlQuery
):
    def get_by_resource_id(
        self,
        resource_id: str,
        version: Optional[int] = None
    ) -> Optional[ResourceDto]:
        stmt = sql.select(ResourceModel).where(
            ResourceModel.resource_id == resource_id)
        row = self._conn.execute(stmt).first()

        return _row_to_dto(row) if row else None

    def get_published_resources(self) -> Iterable[ResourceDto]:
        stmt = sql.select(ResourceModel).where(
            ResourceModel.is_published == True)
        return (
            _row_to_dto(row)
            for row in self._conn.execute(stmt)
        )


def _row_to_dto(row_proxy) -> ResourceDto:
    return ResourceDto(
        id=row_proxy.id,
        resource_id=row_proxy.resource_id,
        version=row_proxy.version,
        config=row_proxy.config,
        is_published=row_proxy.is_published,
        entry_repository_id=row_proxy.entry_repo_id,
        last_modified=row_proxy.last_modified,
        last_modified_by=row_proxy.last_modified_by,
    )
