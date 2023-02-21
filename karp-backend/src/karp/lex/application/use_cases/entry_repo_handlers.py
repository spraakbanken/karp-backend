import logging  # noqa: D100, I001

from karp.command_bus import CommandHandler
from karp.lex.application.repositories.entries import EntryUnitOfWork
from karp.lex import commands
from karp.lex.application import repositories


logger = logging.getLogger(__name__)


class CreatingEntryRepo(CommandHandler[commands.CreateEntryRepository]):  # noqa: D101
    def __init__(  # noqa: D107, ANN204
        self,
        entry_repo_uow: repositories.EntryUowRepositoryUnitOfWork,
        **kwargs,  # noqa: ANN003
    ):
        self._entry_repo_uow = entry_repo_uow

    def execute(  # noqa: D102
        self, command: commands.CreateEntryRepository
    ) -> EntryUnitOfWork:
        entry_repo, events = self._entry_repo_uow.factory.create(
            repository_type=command.repository_type,
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


class DeletingEntryRepository(  # noqa: D101
    CommandHandler[commands.DeleteEntryRepository]
):
    def __init__(  # noqa: D107, ANN204
        self,
        entry_repo_uow: repositories.EntryUowRepositoryUnitOfWork,
        **kwargs,  # noqa: ANN003
    ):
        self._entry_repo_uow = entry_repo_uow

    def execute(self, command: commands.DeleteEntryRepository) -> None:  # noqa: D102
        with self._entry_repo_uow as uow:
            entry_repo = uow.repo.get_by_id(command.id)
            events = entry_repo.discard(user=command.user, timestamp=command.timestamp)
            uow.repo.save(entry_repo)
            uow.post_on_commit(events)
            uow.commit()
