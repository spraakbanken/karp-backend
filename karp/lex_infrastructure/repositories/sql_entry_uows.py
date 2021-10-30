from typing import Optional

from sqlalchemy import orm as sa_orm

from karp.foundation.value_objects import UniqueId
from karp.lex.application.repositories import (
    EntryUnitOfWork,
    EntryUowRepositoryUnitOfWork,
    EntryUowRepository,
)

from karp.db_infrastructure.sql_unit_of_work import SqlUnitOfWork
from karp.db_infrastructure.sql_repository import SqlRepository
from karp.lex_infrastructure.sql.sql_models import EntryUowModel


class SqlEntryUowRepository(EntryUowRepository, SqlRepository):
    def __init__(self, session: sa_orm.Session) -> None:
        EntryUowRepository.__init__(self)
        SqlRepository.__init__(self, session)

    def _save(self, entry_uow: EntryUnitOfWork):
        self._check_has_session()
        self._session.add(
            EntryUowModel.from_entity(entry_uow)
        )

    def _by_id(self, id_: UniqueId) -> Optional[EntryUnitOfWork]:
        return None


class SqlEntryUowRepositoryUnitOfWork(
    SqlUnitOfWork,
    EntryUowRepositoryUnitOfWork
):
    def __init__(self, session_factory: sa_orm.sessionmaker):
        super().__init__()
        self.session_factory = session_factory
        self._repo = None

    def __enter__(self):
        self._session = self.session_factory()
        self._repo = SqlEntryUowRepository(self._session)
        return super().__enter__()

    @property
    def repo(self) -> SqlEntryUowRepository:
        if self._repo is None:
            raise RuntimeError("No resources")
        return self._repo
