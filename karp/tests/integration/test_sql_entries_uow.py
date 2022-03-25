from unittest import mock

import pytest
import ulid

from karp.foundation.events import EventBus
from karp import lex
from karp.lex_infrastructure import SqlEntryUowV1Creator, SqlEntryUowV2Creator
from karp.tests.unit.lex import factories


@pytest.fixture
def example_uow() -> lex.CreateEntryRepository:
    return factories.CreateEntryRepositoryFactory()


@pytest.fixture
def sql_entry_uow_v1_creator(sqlite_session_factory) -> SqlEntryUowV1Creator:
    return SqlEntryUowV1Creator(
        event_bus=mock.Mock(spec=EventBus),
        session_factory=sqlite_session_factory,
    )


@pytest.fixture
def sql_entry_uow_v2_creator(sqlite_session_factory) -> SqlEntryUowV2Creator:
    return SqlEntryUowV2Creator(
        event_bus=mock.Mock(spec=EventBus),
        session_factory=sqlite_session_factory,
    )


class TestSqlEntryUowV1:
    def test_creator_repository_type(
        self,
        sql_entry_uow_v1_creator: SqlEntryUowV1Creator,
    ):
        assert sql_entry_uow_v1_creator.repository_type == "sql_entries_v1"

    def test_uow_repository_type(
        self,
        sql_entry_uow_v1_creator: SqlEntryUowV1Creator,
        example_uow: lex.CreateEntryRepository,
    ):
        entry_uow = sql_entry_uow_v1_creator(
            **example_uow.dict(exclude={"repository_type"})
        )
        assert entry_uow.repository_type == "sql_entries_v1"

    def test_repo_table_name(
        self,
        sql_entry_uow_v1_creator: SqlEntryUowV1Creator,
        example_uow: lex.CreateEntryRepository,
    ):
        entry_uow = sql_entry_uow_v1_creator(
            **example_uow.dict(exclude={"repository_type"})
        )
        with entry_uow as uw:
            assert uw.repo.history_model.__tablename__ == example_uow.name


class TestSqlEntryUowV2:
    def test_creator_repository_type(
        self,
        sql_entry_uow_v2_creator: SqlEntryUowV2Creator,
    ):
        assert sql_entry_uow_v2_creator.repository_type == "sql_entries_v2"

    def test_uow_repository_type(
        self,
        sql_entry_uow_v2_creator: SqlEntryUowV2Creator,
        example_uow: lex.CreateEntryRepository,
    ):
        entry_uow = sql_entry_uow_v2_creator(
            **example_uow.dict(exclude={"repository_type"})
        )
        assert entry_uow.repository_type == "sql_entries_v2"

    def test_repo_table_name(
        self,
        sql_entry_uow_v2_creator: SqlEntryUowV2Creator,
        example_uow: lex.CreateEntryRepository,
    ):
        entry_uow = sql_entry_uow_v2_creator(
            **example_uow.dict(exclude={"repository_type"})
        )
        random_part = ulid.from_uuid(entry_uow.entity_id).randomness().str
        with entry_uow as uw:
            assert (
                uw.repo.history_model.__tablename__
                == f"{example_uow.name}_{random_part}"
            )
