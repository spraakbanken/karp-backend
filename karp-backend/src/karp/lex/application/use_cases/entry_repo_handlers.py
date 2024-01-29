import logging  # noqa: D100, I001

from karp.command_bus import CommandHandler
from karp.lex.application.repositories.entries import EntryUnitOfWork
from karp.lex import commands
from karp.lex.application import repositories


logger = logging.getLogger(__name__)


class CreatingEntryRepo(CommandHandler[commands.CreateEntryRepository]):
    def __init__(
        self,
        entry_repo_uow: repositories.EntryUowRepositoryUnitOfWork,
    ):
        self._entry_repo_uow = entry_repo_uow

    def execute(self, command: commands.CreateEntryRepository) -> EntryUnitOfWork:
        entry_repo, events = self._entry_repo_uow.create(
            id=command.id,
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
            uow.post_on_commit(events)
            uow.commit()
        return entry_repo
