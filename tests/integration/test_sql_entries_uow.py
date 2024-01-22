from unittest import mock  # noqa: I001

import pytest
import ulid

from karp.foundation.events import EventBus
from karp import lex
from karp.lex_infrastructure.repositories import (
    SqlEntryUowCreator,
)
from tests.unit.lex import factories


@pytest.fixture
def example_uow() -> lex.CreateEntryRepository:
    return factories.CreateEntryRepositoryFactory()  # type: ignore [arg-type]


@pytest.fixture
def sql_entry_uow_creator(
    sqlite_session_factory,
) -> SqlEntryUowCreator:
    return SqlEntryUowCreator(
        event_bus=mock.Mock(spec=EventBus),
        session_factory=sqlite_session_factory,
    )


class TestSqlEntryUow:
    def test_repo_table_name(  # noqa: ANN201
        self,
        sql_entry_uow_creator: SqlEntryUowCreator,
        example_uow: lex.CreateEntryRepository,
    ):
        entry_uow, _ = sql_entry_uow_creator.create(**example_uow.dict(exclude={"cmdtype"}))
        random_part = ulid.from_uuid(entry_uow.entity_id).randomness().str
        with entry_uow as uw:
            assert (
                uw.repo.history_model.__tablename__
                == f"{example_uow.name}_{random_part}"
            )
