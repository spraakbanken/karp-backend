import logging
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import sql
from sqlalchemy import orm as sa_orm

from karp.foundation.events import EventBus
from karp.foundation.value_objects import UniqueId
from karp.lex.application.repositories import (
    EntryUnitOfWork,
    EntryUowRepositoryUnitOfWork,
    EntryRepositoryUnitOfWorkFactory,
    EntryUowRepository,
)

from karp.db_infrastructure.sql_unit_of_work import SqlUnitOfWork
from karp.db_infrastructure.sql_repository import SqlRepository
from karp.lex_infrastructure.sql.sql_models import EntryUowModel


logger = logging.getLogger(__name__)


class SqlEntryUowRepository(SqlRepository, EntryUowRepository):
    def __init__(
        self,
        entry_uow_factory: EntryRepositoryUnitOfWorkFactory,
        session: sa_orm.Session,
    ) -> None:
        logger.debug("create repo with session=%s", session)
        EntryUowRepository.__init__(self)  # type: ignore [arg-type]
        SqlRepository.__init__(self, session)
        self.entry_uow_factory = entry_uow_factory

    def _save(self, entry_uow: EntryUnitOfWork):
        logger.debug("saving entry_uow=%s", entry_uow)
        logger.debug("using session=%s", self._session)
        self._check_has_session()
        self._session.add(EntryUowModel.from_entity(entry_uow))
        logger.debug("session=%s, session.new=%s", self._session, self._session.new)

    def _by_id(self, id_: UniqueId, **kwargs) -> Optional[EntryUnitOfWork]:
        # stmt = sql.select(EntryUowModel).where(EntryUowModel.id == id_)
        # row = self._session.execute(stmt).first()
        stmt = (
            self._session.query(EntryUowModel)
            .filter_by(entity_id=id_)
            .order_by(EntryUowModel.last_modified.desc())
        )
        row = stmt.first()
        if row:
            return self._row_to_entity(row)
        return None

    def num_entities(self) -> int:
        self._check_has_session()
        subq = (
            self._session.query(
                EntryUowModel.entity_id,
                sa.func.max(EntryUowModel.last_modified).label("maxdate"),
            )
            .group_by(EntryUowModel.entity_id)
            .subquery("t2")
        )
        query = self._session.query(EntryUowModel).join(
            subq,
            sql.and_(
                EntryUowModel.entity_id == subq.c.entity_id,
                EntryUowModel.last_modified == subq.c.maxdate,
                EntryUowModel.discarded == False,
            ),
        )

        return query.count()

    def _row_to_entity(self, row_proxy) -> EntryUnitOfWork:
        return self.entry_uow_factory.create(
            repository_type=row_proxy.type,
            entity_id=row_proxy.entity_id,
            name=row_proxy.name,
            config=row_proxy.config,
            connection_str=row_proxy.connection_str,
            user=row_proxy.last_modified_by,
            message=row_proxy.message,
            timestamp=row_proxy.last_modified,
        )


class SqlEntryUowRepositoryUnitOfWork(SqlUnitOfWork, EntryUowRepositoryUnitOfWork):
    def __init__(
        self,
        *,
        event_bus: EventBus,
        entry_uow_factory: EntryRepositoryUnitOfWorkFactory,
        session_factory: Optional[sa_orm.sessionmaker] = None,
        session: Optional[sa_orm.Session] = None,
    ):
        SqlUnitOfWork.__init__(self, session=session)
        EntryUowRepositoryUnitOfWork.__init__(
            self,
            event_bus=event_bus,
            entry_uow_factory=entry_uow_factory,
        )
        self.session_factory = session_factory
        if self._session_is_created_here and self.session_factory is None:
            raise ValueError("Must provide one of session and session_factory")
        self._repo = None

    # def __enter__(self):
    #     logger.debug('called __enter__')
    #     if self._session_is_created_here:
    #         self._session = self.session_factory()
    #         logger.debug('created session=%s', self._session)
    #     if self._repo is None:
    #         logger.debug('creating repo')
    #         self._repo = SqlEntryUowRepository(
    #             entry_uow_factory=self.factory,
    #             session=self._session,
    #         )
    #     return super().__enter__()

    def _begin(self):
        logger.debug("called _begin")
        if self._session_is_created_here:
            self._session = self.session_factory()  # type: ignore
            logger.debug("created session=%s", self._session)
        if self._repo is None:
            self._repo = SqlEntryUowRepository(
                entry_uow_factory=self.factory,
                session=self._session,
            )
        return self

    @property
    def repo(self) -> SqlEntryUowRepository:
        if self._repo is None:
            raise RuntimeError("No entry_uow_repository")
        return self._repo
