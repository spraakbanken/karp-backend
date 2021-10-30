from typing import Iterable

from sqlalchemy.sql import select

from karp.lex.application.queries import ListEntryRepos, EntryRepoDto
from karp.lex_infrastructure.queries.base import SqlQuery
from karp.lex_infrastructure.sql.sql_models import EntryUowModel


class SqlListEntryRepos(ListEntryRepos, SqlQuery):
    def query(self) -> Iterable[EntryRepoDto]:
        stmt = select(EntryUowModel)
        return (
            self._row_to_dto(row)
            for row in self._conn.execute(stmt)
        )

    def _row_to_dto(self, row_proxy) -> EntryRepoDto:
        return EntryRepoDto(
            name=row_proxy.name,
            id=row_proxy.id,
            repository_type=row_proxy.type,
        )
