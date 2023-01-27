from typing import Iterable, Optional

from sqlalchemy.sql import select

from karp.lex import ListEntryRepos, EntryRepoDto, ReadOnlyEntryRepoRepositry
from karp.lex_infrastructure.queries.base import SqlQuery
from karp.lex_infrastructure.sql.sql_models import EntryUowModel


class SqlListEntryRepos(ListEntryRepos, SqlQuery):
    def query(self) -> Iterable[EntryRepoDto]:
        stmt = select(EntryUowModel)
        return (_row_to_dto(row) for row in self._conn.execute(stmt))


def _row_to_dto(row_proxy) -> EntryRepoDto:
    return EntryRepoDto(
        name=row_proxy.name,
        entity_id=row_proxy.entity_id,
        repository_type=row_proxy.type,
    )


class SqlReadOnlyEntryRepoRepositry(SqlQuery, ReadOnlyEntryRepoRepositry):
    def get_by_name(self, name: str) -> Optional[EntryRepoDto]:
        stmt = select(EntryUowModel).filter_by(name=name)

        row = self._conn.execute(stmt).first()

        return _row_to_dto(row) if row else None
