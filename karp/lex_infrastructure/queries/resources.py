from typing import Iterable

from sqlalchemy import sql

from karp.lex.application.queries import GetPublishedResources, ResourceDto
from karp.lex_infrastructure.sql.sql_models import ResourceModel
from karp.lex_infrastructure.queries.base import SqlQuery


class SqlGetPublishedResources(
    GetPublishedResources,
    SqlQuery
):
    def query(self) -> Iterable[ResourceDto]:
        stmt = sql.select(ResourceModel).where(ResourceModel.is_published == True)
        return (
            self._row_to_dto(row)
            for row in self._conn.execute(stmt)
        )

    def _row_to_dto(self, row_proxy) -> ResourceDto:
        return ResourceDto(
            resource_id=row_proxy.resource_id,
        )
