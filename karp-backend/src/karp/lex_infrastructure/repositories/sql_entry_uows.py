import logging  # noqa: D100, I001
from typing import Optional, Tuple

from sqlalchemy import orm as sa_orm, text

from karp.foundation.events import EventBus, Event
from karp.foundation.repository import Repository
from karp.lex_core.value_objects import UniqueId
from karp.lex.application.repositories import (
    EntryUnitOfWork,
    EntryUowRepositoryUnitOfWork,
)

from karp.db_infrastructure.sql_unit_of_work import SqlUnitOfWork
from karp.db_infrastructure.sql_repository import SqlRepository
from karp.lex_infrastructure.sql.sql_models import EntryUowModel
from karp.lex_infrastructure.repositories.sql_entries import SqlEntryUnitOfWork


logger = logging.getLogger(__name__)

class SqlEntryUowRepository(SqlRepository, Repository):  # noqa: D101
    def __init__(  # noqa: D107
        self,
        session: sa_orm.Session,
        event_bus: EventBus,
    ) -> None:
        logger.debug("create repo with session=%s", session)
        SqlRepository.__init__(self, session)
        self.event_bus = event_bus

    def _save(self, entry_uow: EntryUnitOfWork):  # noqa: ANN202
        logger.debug("saving entry_uow=%s", entry_uow)
        logger.debug("using session=%s", self._session)
        self._check_has_session()
        self._session.add(EntryUowModel.from_entity(entry_uow))
        if entry_uow.discarded:
            # If resource was discarded, drop the table containing all data entries
            self._session.execute(text("DROP table " + entry_uow.table_name()))
        logger.debug("session=%s, session.new=%s", self._session, self._session.new)

    def _by_id(
        self,
        id: UniqueId,  # noqa: A002
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
        return SqlEntryUnitOfWork.create(
            session=self._session,
            event_bus=self.event_bus,
            id=row_proxy.entity_id,
            name=row_proxy.name,
            config=row_proxy.config,
            connection_str=row_proxy.connection_str,
            user=row_proxy.last_modified_by,
            message=row_proxy.message,
            timestamp=row_proxy.last_modified,
        )


class SqlEntryUowRepositoryUnitOfWork(  # noqa: D101
    SqlUnitOfWork, EntryUowRepositoryUnitOfWork
):
    def __init__(  # noqa: D107, ANN204
        self,
        *,
        event_bus: EventBus,
        session: sa_orm.Session,
    ):
        SqlUnitOfWork.__init__(self, session=session)
        EntryUowRepositoryUnitOfWork.__init__(
            self,
            event_bus=event_bus,
        )
        self._repo = None

    def _begin(self):  # noqa: ANN202
        logger.debug("called _begin")
        if self._repo is None:
            self._repo = SqlEntryUowRepository(
                session=self._session,
                event_bus=self.event_bus,
            )
        return self

    @property
    def repo(self) -> SqlEntryUowRepository:  # noqa: D102
        if self._repo is None:
            raise RuntimeError("No entry_uow_repository")
        return self._repo

    def create(self, *args, **kwargs) -> Tuple[EntryUnitOfWork, list[Event]]:
        return SqlEntryUnitOfWork.create(
            *args, **kwargs,
            session=self._session,
            event_bus=self.event_bus
        ), []
