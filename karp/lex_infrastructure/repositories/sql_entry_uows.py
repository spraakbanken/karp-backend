from typing import Optional

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


class SqlEntryUowRepository(EntryUowRepository, SqlRepository):
    def __init__(
        self,
        entry_uow_factory: EntryRepositoryUnitOfWorkFactory,
        session: sa_orm.Session
    ) -> None:
        EntryUowRepository.__init__(self)
        SqlRepository.__init__(self, session)
        self.entry_uow_factory = entry_uow_factory

    def _save(self, entry_uow: EntryUnitOfWork):
        self._check_has_session()
        self._session.add(
            EntryUowModel.from_entity(entry_uow)
        )

    def _by_id(self, id_: UniqueId, **kwargs) -> Optional[EntryUnitOfWork]:
        # stmt = sql.select(EntryUowModel).where(EntryUowModel.id == id_)
        # row = self._session.execute(stmt).first()
        stmt = self._session.query(
            EntryUowModel
        ).filter_by(id=id_).order_by(EntryUowModel.last_modified.desc())
        row = stmt.first()
        if row:
            return self._row_to_entity(row)
        return None

    def _row_to_entity(self, row_proxy) -> EntryUnitOfWork:
        return self.entry_uow_factory.create(
            repository_type=row_proxy.type,
            entity_id=row_proxy.id,
            name=row_proxy.name,
            config=row_proxy.config,
            connection_str=row_proxy.connection_str,
            user=row_proxy.last_modified_by,
            message=row_proxy.message,
            timestamp=row_proxy.last_modified,
        )


class SqlEntryUowRepositoryUnitOfWork(
    SqlUnitOfWork,
    EntryUowRepositoryUnitOfWork
):
    def __init__(
        self,
        session_factory: sa_orm.sessionmaker,
        event_bus: EventBus,
        entry_uow_factory: EntryRepositoryUnitOfWorkFactory,
    ):
        SqlUnitOfWork.__init__(self)
        EntryUowRepositoryUnitOfWork.__init__(self, event_bus)
        self.session_factory = session_factory
        self.entry_uow_factory = entry_uow_factory
        self._repo = None
        self._session = None

    def __enter__(self):
        if self._session is None:
            self._session = self.session_factory()
        if self._repo is None:
            self._repo = SqlEntryUowRepository(
                entry_uow_factory=self.entry_uow_factory,
                session=self._session,
            )
        return super().__enter__()

    def _begin(self):
        if self._session is None:
            self._session = self.session_factory()
        if self._repo is None:
            self._repo = SqlEntryUowRepository(
                entry_uow_factory=self.entry_uow_factory,
                session=self._session,
            )
        return self

    @property
    def repo(self) -> SqlEntryUowRepository:
        if self._repo is None:
            raise RuntimeError("No entry_uow_repository")
        return self._repo
