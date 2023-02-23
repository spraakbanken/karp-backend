"""Handling of entry commands."""
import logging

from karp.command_bus import CommandHandler
from karp.lex.application import repositories
from karp.lex.application.repositories import EntryUnitOfWork
from karp.lex.domain import errors
from karp.lex_core import commands
from karp.lex_core.value_objects import unique_id

logger = logging.getLogger(__name__)


class BaseEntryHandler:  # noqa: D101
    def __init__(  # noqa: D107
        self,
        entry_repo_uow: repositories.EntryUowRepositoryUnitOfWork,
        resource_uow: repositories.ResourceUnitOfWork,
    ) -> None:
        super().__init__()
        self.entry_repo_uow = entry_repo_uow
        self.resource_uow = resource_uow

    def get_entry_uow(  # noqa: D102
        self, entry_repo_id: unique_id.UniqueId
    ) -> EntryUnitOfWork:
        with self.entry_repo_uow as uw:
            return uw.repo.get_by_id(entry_repo_id)


class AddingEntry(BaseEntryHandler, CommandHandler[commands.AddEntry]):  # noqa: D101
    def __init__(
        self,
        entry_repo_uow: repositories.EntryUowRepositoryUnitOfWork,
        resource_uow: repositories.ResourceUnitOfWork,
    ) -> None:
        """Usecase for adding an entry."""
        super().__init__(
            entry_repo_uow=entry_repo_uow,
            resource_uow=resource_uow,
        )

    def execute(self, command: commands.AddEntry):  # noqa: ANN201, D102
        with self.resource_uow:
            resource = self.resource_uow.repo.by_resource_id(command.resource_id)

        entry_uow = self.get_entry_uow(resource.entry_repository_id)
        with entry_uow as uw:
            entry, events = resource.create_entry_from_dict(
                command.entry,  # type: ignore [arg-type]
                user=command.user,
                message=command.message,
                id=command.id,
                timestamp=command.timestamp,
            )
            uw.entries.save(entry)
            uw.post_on_commit(events)
            uw.commit()
        return entry


class UpdatingEntry(BaseEntryHandler, CommandHandler[commands.UpdateEntry]):
    """Usecase for updating an entry."""

    def __init__(
        self,
        entry_repo_uow: repositories.EntryUowRepositoryUnitOfWork,
        resource_uow: repositories.ResourceUnitOfWork,
    ) -> None:
        """Create usecase for updating an entry."""
        super().__init__(
            entry_repo_uow=entry_repo_uow,
            resource_uow=resource_uow,
        )

    def execute(self, command: commands.UpdateEntry):  # noqa: ANN201, D102
        with self.resource_uow:
            resource = self.resource_uow.repo.by_resource_id(command.resource_id)

        with self.get_entry_uow(resource.entry_repository_id) as uw:
            try:
                current_db_entry = uw.repo.by_id(command.id)
            except errors.EntryNotFound as err:
                raise errors.EntryNotFound(
                    command.resource_id,
                    id=command.id,
                ) from err

            events = resource.update_entry(
                entry=current_db_entry,
                body=command.entry,  # type: ignore [arg-type]
                version=command.version,
                user=command.user,
                message=command.message,
                timestamp=command.timestamp,
            )
            uw.repo.save(current_db_entry)
            uw.post_on_commit(events)
            uw.commit()

        return current_db_entry


class AddingEntries(BaseEntryHandler, CommandHandler[commands.AddEntries]):
    """Adding entries."""

    def execute(self, command: commands.AddEntries):  # noqa: ANN201
        """
        Add entries to DB and INDEX (if present and resource is active).

        Raises
        ------
        RuntimeError
            If the resource.entry_schema fails to compile.
        KarpError
            - If an entry fails to be validated against the json schema.
            - If the DB interaction fails.

        Returns
        -------
        List
            List of the id's of the created entries.
        """  # noqa: D202, D212

        if not isinstance(command.resource_id, str):
            raise ValueError(
                f"'resource_id' must be of type 'str', were '{type(command.resource_id)}'"
            )
        with self.resource_uow:
            resource = self.resource_uow.resources.by_resource_id(command.resource_id)

        if not resource:
            raise errors.ResourceNotFound(command.resource_id)

        created_db_entries = []
        with self.entry_repo_uow, self.entry_repo_uow.repo.get_by_id(
            resource.entry_repository_id
        ) as uw:
            for i, entry_raw in enumerate(command.entries):

                entry, events = resource.create_entry_from_dict(
                    entry_raw,
                    user=command.user,
                    message=command.message,
                    id=unique_id.make_unique_id(),
                )
                uw.repo.save(entry)
                created_db_entries.append(entry)

                uw.post_on_commit(events)
                if command.chunk_size > 0 and i % command.chunk_size == 0:
                    uw.commit()
            uw.commit()

        return created_db_entries


class ImportingEntries(  # noqa: D101
    BaseEntryHandler, CommandHandler[commands.ImportEntries]
):
    def execute(self, command: commands.ImportEntries):  # noqa: ANN201
        """
        Import entries to DB and INDEX (if present and resource is active).

        Raises
        ------
        RuntimeError
            If the resource.entry_schema fails to compile.
        KarpError
            - If an entry fails to be validated against the json schema.
            - If the DB interaction fails.

        Returns
        -------
        List
            List of the id's of the created entries.
        """  # noqa: D202, D212

        if not isinstance(command.resource_id, str):
            raise ValueError(
                f"'resource_id' must be of type 'str', were '{type(command.resource_id)}'"
            )
        with self.resource_uow:
            resource = self.resource_uow.resources.by_resource_id(command.resource_id)

        if not resource:
            raise errors.ResourceNotFound(command.resource_id)

        created_db_entries = []
        with self.entry_repo_uow, self.entry_repo_uow.repo.get_by_id(
            resource.entry_repository_id
        ) as uw:
            for i, entry_raw in enumerate(command.entries):

                entry, events = resource.create_entry_from_dict(
                    entry_raw["entry"],
                    user=entry_raw.get("user") or command.user,
                    message=entry_raw.get("message") or command.message,
                    id=entry_raw.get("id") or unique_id.make_unique_id(),
                    timestamp=entry_raw.get("last_modified"),
                )
                uw.entries.save(entry)
                uw.post_on_commit(events)
                created_db_entries.append(entry)

                if command.chunk_size > 0 and i % command.chunk_size == 0:
                    uw.commit()
            uw.commit()

        return created_db_entries


class DeletingEntry(BaseEntryHandler, CommandHandler[commands.DeleteEntry]):
    """Use case for deleting an entry."""

    def execute(self, command: commands.DeleteEntry) -> None:  # noqa: D102
        with self.resource_uow:
            resource = self.resource_uow.repo.by_resource_id(command.resource_id)

        with self.entry_repo_uow, self.entry_repo_uow.repo.get_by_id(
            resource.entry_repository_id
        ) as uw:
            entry = uw.repo.by_id(command.id)

            events = resource.discard_entry(
                entry=entry,
                version=command.version,
                user=command.user,
                message=command.message or "Entry deleted.",
                timestamp=command.timestamp,
            )
            uw.repo.save(entry)
            uw.post_on_commit(events)
            uw.commit()
