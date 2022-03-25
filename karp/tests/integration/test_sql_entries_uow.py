from unittest import mock

import pytest

from karp.foundation.events import EventBus
from karp import lex
from karp.lex_infrastructure import SqlEntryUowCreator
from karp.tests.unit.lex import factories


@pytest.fixture
def example_uow() -> lex.CreateEntryRepository:
    return factories.CreateEntryRepositoryFactory()


@pytest.fixture
def sql_entry_uow_v1_creator(sqlite_session_factory) -> SqlEntryUowCreator:
    return SqlEntryUowCreator(
        event_bus=mock.Mock(spec=EventBus),
        session_factory=sqlite_session_factory,
    )


class TestSqlEntryUowV1:
    def test_creator_repository_type(
        self,
        sql_entry_uow_v1_creator: SqlEntryUowCreator,
    ):
        assert sql_entry_uow_v1_creator.repository_type == 'sql_entries_v1'

    def test_uow_repository_type(
        self,
        sql_entry_uow_v1_creator: SqlEntryUowCreator,
        example_uow: lex.CreateEntryRepository,
    ):
        entry_uow = sql_entry_uow_v1_creator(
            **example_uow.dict(exclude={'repository_type'})
        )
        assert entry_uow.repository_type == 'sql_entries_v1'

    def test_repo_table_name(
        self,
        sql_entry_uow_v1_creator: SqlEntryUowCreator,
        example_uow: lex.CreateEntryRepository,
    ):
        entry_uow = sql_entry_uow_v1_creator(
            **example_uow.dict(exclude={'repository_type'})
        )
        with entry_uow as uw:
            assert uw.repo.history_model.__tablename__ == example_uow.name

