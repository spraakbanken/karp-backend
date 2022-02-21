
from karp.lex.application.repositories import (
    EntryUowRepositoryUnitOfWork,
)

from . import adapters, factories


class TestCreateEntryRepository:
    def test_create_entry_repository(
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd = factories.CreateEntryRepositoryFactory()
        lex_ctx.command_bus.dispatch(cmd)

        entry_uow_repo_uow = lex_ctx.container.get(
            EntryUowRepositoryUnitOfWork)
        assert entry_uow_repo_uow.was_committed
        assert len(entry_uow_repo_uow.repo) == 1
