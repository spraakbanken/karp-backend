from typing import Iterable, Optional  # noqa: D100, I001

import sqlalchemy as sa
from sqlalchemy import sql
from karp.lex_core.value_objects.unique_id import UniqueId

from karp.lex.application.queries import (
    GetPublishedResources,
    ResourceDto,
    GetResources,
)
from karp.lex.application.queries.resources import ReadOnlyResourceRepository
from karp.lex_infrastructure.sql.sql_models import ResourceModel
from karp.lex_infrastructure.queries.base import SqlQuery


class SqlGetPublishedResources(GetPublishedResources, SqlQuery):  # noqa: D101
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
        return (_row_to_dto(row) for row in self._conn.execute(stmt))


class SqlGetResources(GetResources, SqlQuery):  # noqa: D101
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
        return [_row_to_dto(row) for row in self._conn.execute(stmt)]


class SqlReadOnlyResourceRepository(ReadOnlyResourceRepository, SqlQuery):  # noqa: D101
    def get_by_id(  # noqa: D102
        self, entity_id: UniqueId, version: Optional[int] = None
    ) -> Optional[ResourceDto]:
        filters: dict[str, UniqueId | str | int] = {"entity_id": entity_id}
        if version:
            filters["version"] = version
        stmt = (
            sql.select(ResourceModel)
            .filter_by(**filters)
            .order_by(ResourceModel.last_modified.desc())
        )
        print(f"stmt={str(stmt)}")
        row = self._conn.execute(stmt).first()

        return _row_to_dto(row) if row else None

    def _get_by_resource_id(self, resource_id: str) -> Optional[ResourceDto]:
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
                ResourceModel.resource_id == resource_id,
            ),
        )
        stmt = stmt.order_by(ResourceModel.last_modified.desc())
        row = self._conn.execute(stmt).first()

        return _row_to_dto(row) if row else None

    def get_published_resources(self) -> Iterable[ResourceDto]:  # noqa: D102
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
        return (_row_to_dto(row) for row in self._conn.execute(stmt))

    def get_all_resources(self) -> Iterable[ResourceDto]:  # noqa: D102
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
        return (_row_to_dto(row) for row in self._conn.execute(stmt))


def _row_to_dto(row_proxy) -> ResourceDto:
    return ResourceDto(
        id=row_proxy.entity_id,
        resourceId=row_proxy.resource_id,
        version=row_proxy.version,
        config=row_proxy.config,
        isPublished=row_proxy.is_published,
        entryRepositoryId=row_proxy.entry_repo_id,
        lastModified=row_proxy.last_modified,
        lastModifiedBy=row_proxy.last_modified_by,
        message=row_proxy.message,
        name=row_proxy.name,
        discarded=row_proxy.discarded,
    )
