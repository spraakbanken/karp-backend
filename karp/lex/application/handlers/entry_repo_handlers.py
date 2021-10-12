from karp.lex.domain import commands
from karp.lex.application import unit_of_work


class CreateEntryRepositoryHandler:
    def __init__(
        self,
        entry_repo_repo_uow: unit_of_work.EntryRepositoryRepositoryUnitOfWork,
        entry_repo_uow_factory: unit_of_work.EntryRepositoryUnitOfWorkFactory
    ):
        self._entry_repo_repo_uow = entry_repo_repo_uow
        self._entry_repo_uow_factory = entry_repo_uow_factory

    def __call__(
        self,
        command: commands.CreateEntryRepository
    ) -> None:
        entry_repo = self._entry_repo_uow_factory.create(
            repository_type=command.repository_type,
            entity_id=command.entity_id,
            name=command.name,
            config=command.config,
        )
        with self._entry_repo_repo_uow as uow:
            uow.commit()


