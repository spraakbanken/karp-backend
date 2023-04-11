from karp.lex.application.repositories import (
    EntryUowRepositoryUnitOfWork,
)

from . import adapters, factories


class TestCreateEntryRepository:
    def test_create_entry_repository(  # noqa: ANN201
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd = factories.CreateEntryRepositoryFactory()
        lex_ctx.command_bus.dispatch(cmd)

        entry_uow_repo_uow = lex_ctx.container.get(EntryUowRepositoryUnitOfWork)  # type: ignore [misc]
        assert entry_uow_repo_uow.was_committed  # type: ignore [attr-defined]
