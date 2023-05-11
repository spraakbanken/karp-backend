import logging  # noqa: D100, I001
from typing import Optional

from sqlalchemy import orm as sa_orm

from karp.foundation.events import EventBus
from karp.lex_core.value_objects import UniqueId
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


class SqlEntryUowRepository(SqlRepository, EntryUowRepository):  # noqa: D101
    def __init__(  # noqa: D107
        self,
        entry_uow_factory: EntryRepositoryUnitOfWorkFactory,
        session: sa_orm.Session,
    ) -> None:
        logger.debug("create repo with session=%s", session)
        EntryUowRepository.__init__(self)  # type: ignore [arg-type]
        SqlRepository.__init__(self, session)
        self.entry_uow_factory = entry_uow_factory

    def _save(self, entry_uow: EntryUnitOfWork):  # noqa: ANN202
        logger.debug("saving entry_uow=%s", entry_uow)
        logger.debug("using session=%s", self._session)
        self._check_has_session()
        self._session.add(EntryUowModel.from_entity(entry_uow))
        if entry_uow.discarded : 
            # If resource was discarded, drop the table containing all data entries
            self._session.execute('DROP table ' + entry_uow.table_name())
        logger.debug("session=%s, session.new=%s", self._session, self._session.new)

    def _by_id(
        self,
        id: UniqueId,
        *,
        version: Optional[int] = None,
        **kwargs,
    ) -> Optional[EntryUnitOfWork]:
        stmt = (
            self._session.query(EntryUowModel)
            .filter_by(entity_id=id)
            .order_by(EntryUowModel.last_modified.desc())
        )
        return self._row_to_entity(row) if (row := stmt.first()) else None

    def _row_to_entity(self, row_proxy) -> EntryUnitOfWork:
        uow, _events = self.entry_uow_factory.create(
            id=row_proxy.entity_id,
            name=row_proxy.name,
            config=row_proxy.config,
            connection_str=row_proxy.connection_str,
            user=row_proxy.last_modified_by,
            message=row_proxy.message,
            timestamp=row_proxy.last_modified,
        )
        return uow


class SqlEntryUowRepositoryUnitOfWork(  # noqa: D101
    SqlUnitOfWork, EntryUowRepositoryUnitOfWork
):
    def __init__(  # noqa: D107, ANN204
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

    def _begin(self):  # noqa: ANN202
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
    def repo(self) -> SqlEntryUowRepository:  # noqa: D102
        if self._repo is None:
            raise RuntimeError("No entry_uow_repository")
        return self._repo
