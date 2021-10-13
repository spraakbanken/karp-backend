
from karp.lex.application.handlers import (
    CreateEntryRepositoryHandler,
)
from karp.lex.domain.commands import CreateEntryRepository

from karp.tests.unit.adapters import (
    FakeEntryUowRepositoryUnitOfWork,
    FakeEntryRepositoryUnitOfWorkFactory,
)


class TestCreateEntryRepository:
    def test_create_entry_repository(
        self,
        create_entry_repository: CreateEntryRepository,
        entry_repo_repo_uow: FakeEntryUowRepositoryUnitOfWork,
        entry_repo_uow_factory: FakeEntryRepositoryUnitOfWorkFactory,
    ):
        cmd_handler = CreateEntryRepositoryHandler(
            entry_repo_repo_uow,
            entry_repo_uow_factory,
        )
        cmd_handler(create_entry_repository)

        assert entry_repo_repo_uow.was_committed
        assert len(entry_repo_repo_uow.repo) == 1
