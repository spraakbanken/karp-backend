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

        entry_uow_repo_uow = lex_ctx.container.get(EntryUowRepositoryUnitOfWork)  # type: ignore [misc]
        assert entry_uow_repo_uow.was_committed  # type: ignore [attr-defined]
        assert entry_uow_repo_uow.repo.num_entities() == 1


class TestDeleteEntryRepository:
    def test_delete_entry_repository_succeeds(
        self,
        lex_ctx: adapters.UnitTestContext,
    ):
        cmd = factories.CreateEntryRepositoryFactory()
        lex_ctx.command_bus.dispatch(cmd)

        entry_uow_repo_uow = lex_ctx.container.get(EntryUowRepositoryUnitOfWork)  # type: ignore [misc]
        assert entry_uow_repo_uow.repo.num_entities() == 1

        cmd = factories.DeleteEntryRepositoryFactory(entity_id=cmd.entity_id)
        lex_ctx.command_bus.dispatch(cmd)
        assert entry_uow_repo_uow.repo.num_entities() == 0
