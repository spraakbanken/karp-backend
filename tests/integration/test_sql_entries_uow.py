from unittest import mock  # noqa: I001

import pytest
import ulid

from karp.foundation.events import EventBus
from karp import lex
from karp.lex_infrastructure.repositories import (
    SqlEntryUowV2Creator,
)
from tests.unit.lex import factories


@pytest.fixture
def example_uow() -> lex.CreateEntryRepository:
    return factories.CreateEntryRepositoryFactory()  # type: ignore [arg-type]


@pytest.fixture
def sql_entry_uow_v2_creator(
    sqlite_session_factory,
) -> SqlEntryUowV2Creator:
    return SqlEntryUowV2Creator(
        event_bus=mock.Mock(spec=EventBus),
        session_factory=sqlite_session_factory,
    )


class TestSqlEntryUowV2:
    def test_repo_table_name(  # noqa: ANN201
        self,
        sql_entry_uow_v2_creator: SqlEntryUowV2Creator,
        example_uow: lex.CreateEntryRepository,
    ):
        entry_uow, _ = sql_entry_uow_v2_creator(**example_uow.dict(exclude={"cmdtype"}))
        random_part = ulid.from_uuid(entry_uow.entity_id).randomness().str
        with entry_uow as uw:
            assert (
                uw.repo.history_model.__tablename__
                == f"{example_uow.name}_{random_part}"
            )
