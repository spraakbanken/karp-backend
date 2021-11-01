from typing import Iterable

from sqlalchemy import sql

from karp.lex.application.queries import GetPublishedResources, ResourceDto, GetResources
from karp.lex_infrastructure.sql.sql_models import ResourceModel
from karp.lex_infrastructure.queries.base import SqlQuery


class SqlGetPublishedResources(
    GetPublishedResources,
    SqlQuery
):
    def query(self) -> Iterable[ResourceDto]:
        stmt = sql.select(ResourceModel).where(ResourceModel.is_published == True)
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


def _row_to_dto(row_proxy) -> ResourceDto:
    return ResourceDto(
        id=row_proxy.id,
        resource_id=row_proxy.resource_id,
        version=row_proxy.version,
        is_published=row_proxy.is_published,
        last_modified=row_proxy.last_modified,
        last_modified_by=row_proxy.last_modified_by,
    )
