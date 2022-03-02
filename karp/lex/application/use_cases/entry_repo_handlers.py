import logging

from karp.foundation.commands import CommandHandler
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

    def execute(
        self,
        command: commands.CreateEntryRepository
    ) -> None:
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

        logger.debug('Created entry repo', extra={'entry_repo': entry_repo})
        with self._entry_repo_uow as uow:
            logger.debug('Saving...')
            uow.repo.save(entry_repo)
            uow.commit()
        return entry_repo
