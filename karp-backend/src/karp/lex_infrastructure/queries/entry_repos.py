from typing import Iterable, Optional  # noqa: D100, I001

from sqlalchemy.sql import select

from karp.lex import ListEntryRepos, EntryRepoDto, ReadOnlyEntryRepoRepository
from karp.lex_infrastructure.queries.base import SqlQuery
from karp.lex_infrastructure.sql.sql_models import EntryUowModel


class SqlListEntryRepos(ListEntryRepos, SqlQuery):  # noqa: D101
    def query(self) -> Iterable[EntryRepoDto]:  # noqa: D102
        stmt = select(EntryUowModel)
        return (_row_to_dto(row) for row in self._conn.execute(stmt))


def _row_to_dto(row_proxy) -> EntryRepoDto:
    return EntryRepoDto(
        name=row_proxy.name,
        entity_id=row_proxy.entity_id,
        repository_type=row_proxy.type,
    )


class SqlReadOnlyEntryRepoRepository(  # noqa: D101
    SqlQuery, ReadOnlyEntryRepoRepository
):
    def get_by_name(self, name: str) -> Optional[EntryRepoDto]:  # noqa: D102
        stmt = select(EntryUowModel).filter_by(name=name)

        row = self._conn.execute(stmt).first()

        return _row_to_dto(row) if row else None
