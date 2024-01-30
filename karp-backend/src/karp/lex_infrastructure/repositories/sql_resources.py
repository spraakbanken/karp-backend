"""SQL Resource Repository"""  # noqa: D400, D415
import logging  # noqa: I001
import typing
from typing import List, Optional, Union
from karp.lex_core.value_objects import UniqueId

import sqlalchemy as sa
from sqlalchemy import sql
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, text

from karp.foundation.events import EventBus
from karp.lex.domain import entities
from karp.lex.application import repositories
from karp.lex.domain.entities.resource import Resource

from karp.db_infrastructure.sql_unit_of_work import SqlUnitOfWork
from karp.lex_infrastructure.sql.sql_models import ResourceModel
from karp.db_infrastructure.sql_repository import SqlRepository
from karp.lex_infrastructure.repositories.sql_entries import SqlEntryUnitOfWork

logger = logging.getLogger(__name__)


class SqlResourceRepository(  # noqa: D101
    SqlRepository, repositories.ResourceRepository
):
    def __init__(self, session: Session):  # noqa: D107, ANN204
        repositories.ResourceRepository.__init__(self)
        SqlRepository.__init__(self, session=session)

    def _save(self, resource: Resource):  # noqa: ANN202
        self._check_has_session()
        resource_dto = ResourceModel.from_entity(resource)
        self._session.add(resource_dto)
        if resource.discarded:
            # If resource was discarded, drop the table containing all data entries
            self._session.execute(text("DROP table " + resource.table_name))

    def resource_ids(self) -> List[str]:  # noqa: D102
        self._check_has_session()
        subq = (
            sql.select(
                ResourceModel.entity_id,
                sa.func.max(ResourceModel.last_modified).label("maxdate"),
            )
            .group_by(ResourceModel.entity_id)
            .subquery("t2")
        )

        stmt = sql.select(ResourceModel.resource_id).join(
            subq,
            sa.and_(
                ResourceModel.entity_id == subq.c.entity_id,
                ResourceModel.last_modified == subq.c.maxdate,
                ResourceModel.discarded == False,  # noqa: E712
            ),
        )
        return self._session.execute(stmt).scalars().all()

    def _by_id(
        self,
        id: Union[UniqueId, str],  # noqa: A002
        *,
        version: Optional[int] = None,
        **kwargs,  # noqa: ANN003
    ) -> typing.Optional[entities.Resource]:
        self._check_has_session()
        query = self._session.query(ResourceModel).filter_by(entity_id=id)
        if version:
            query = query.filter_by(version=version)
        else:
            query = query.order_by(ResourceModel.version.desc())
        resource_dto = query.first()
        return resource_dto.to_entity() if resource_dto else None

    def _by_resource_id(
        self,
        resource_id: str,
    ) -> Optional[Resource]:
        self._check_has_session()
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

        query = self._session.execute(stmt).scalars()
        resource_dto = query.first()
        return resource_dto.to_entity() if resource_dto else None

    def _get_published_resources(self) -> typing.List[entities.Resource]:
        self._check_has_session()
        subq = (
            self._session.query(
                ResourceModel.resource_id,
                func.max(ResourceModel.last_modified).label("maxdate"),
            )
            .group_by(ResourceModel.resource_id)
            .subquery("t2")
        )
        query = self._session.query(ResourceModel).join(
            subq,
            and_(
                ResourceModel.resource_id == subq.c.resource_id,
                ResourceModel.last_modified == subq.c.maxdate,
                ResourceModel.is_published == True,  # noqa: E712
            ),
        )

        return [resource_dto.to_entity() for resource_dto in query if resource_dto is not None]

    def _get_all_resources(self) -> typing.List[entities.Resource]:
        self._check_has_session()
        subq = (
            self._session.query(
                ResourceModel.resource_id,
                func.max(ResourceModel.last_modified).label("maxdate"),
            )
            .group_by(ResourceModel.resource_id)
            .subquery("t2")
        )
        query = self._session.query(ResourceModel).join(
            subq,
            and_(
                ResourceModel.resource_id == subq.c.resource_id,
                ResourceModel.last_modified == subq.c.maxdate,
            ),
        )

        return [resource_dto.to_entity() for resource_dto in query if resource_dto is not None]


class SqlResourceUnitOfWork(  # noqa: D101
    SqlUnitOfWork, repositories.ResourceUnitOfWork
):
    def __init__(  # noqa: D107, ANN204
        self,
        event_bus: EventBus,
        *,
        session: Session,
    ):
        SqlUnitOfWork.__init__(self, session=session)
        repositories.ResourceUnitOfWork.__init__(self, event_bus)
        self._resources = None

    def _begin(self):  # noqa: ANN202
        if self._resources is None:
            logger.info("using session", extra={"session": self._session})
            self._resources = SqlResourceRepository(self._session)
        return self

    @property
    def repo(self) -> SqlResourceRepository:  # noqa: D102
        self._begin()
        return self._resources

    def resource_to_entry_uow(self, resource: Resource) -> SqlEntryUnitOfWork:
        return SqlEntryUnitOfWork(
            session=self._session, event_bus=self.event_bus, resource=resource
        )
