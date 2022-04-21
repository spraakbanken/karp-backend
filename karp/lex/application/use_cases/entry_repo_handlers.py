import logging
from typing import Any

from karp.foundation.commands import CommandHandler
from karp.lex.application.repositories.entries import EntryUnitOfWork
from karp.lex.domain import commands
from karp.lex.application import repositories


logger = logging.getLogger(__name__)


class CreatingEntryRepo(CommandHandler[commands.CreateEntryRepository]):
    def __init__(
        self,
        entry_repo_uow: repositories.EntryUowRepositoryUnitOfWork,
        **kwargs,
    ):
        self._entry_repo_uow = entry_repo_uow

    def execute(self, command: commands.CreateEntryRepository) -> EntryUnitOfWork:
        entry_repo = self._entry_repo_uow.factory.create(
            repository_type=command.repository_type,
            entity_id=command.entity_id,
            name=command.name,
            config=command.config,
            connection_str=command.connection_str,
            user=command.user,
            timestamp=command.timestamp,
            message=command.message,
        )

        logger.debug("Created entry repo", extra={"entry_repo": entry_repo})
        with self._entry_repo_uow as uow:
            logger.debug("Saving...")
            uow.repo.save(entry_repo)
            uow.commit()
        return entry_repo


class DeletingEntryRepository(CommandHandler[commands.DeleteEntryRepository]):
    def __init__(
        self,
        entry_repo_uow: repositories.EntryUowRepositoryUnitOfWork,
        **kwargs,
    ):
        self._entry_repo_uow = entry_repo_uow

    def execute(self, command: commands.DeleteEntryRepository) -> None:
        with self._entry_repo_uow as uow:
            entry_repo = uow.repo.get_by_id(command.entity_id)
            entry_repo.discard(user=command.user, timestamp=command.timestamp)
            uow.repo.save(entry_repo)
            uow.commit()
