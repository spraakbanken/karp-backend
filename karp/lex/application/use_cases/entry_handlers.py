import logging
import typing
from pathlib import Path

import json_streams
from sb_json_tools import jsondiff
import logging

from karp.foundation.commands import CommandHandler
from karp.lex.application.repositories import EntryUnitOfWork
from karp.lex.domain import errors
from karp.lex.domain.entities.entry import Entry
from karp.foundation.value_objects import unique_id

from karp.foundation import events as foundation_events
from karp.lex.domain import commands
from karp.lex.domain.value_objects import EntrySchema
from karp.lex.application import repositories


logger = logging.getLogger(__name__)


class BasingEntry:
    def __init__(
        self,
        entry_repo_uow: repositories.EntryUowRepositoryUnitOfWork,
        resource_uow: repositories.ResourceUnitOfWork,
    ) -> None:
        super().__init__()
        self.entry_repo_uow = entry_repo_uow
        self.resource_uow = resource_uow

    def collect_new_events(self) -> typing.Iterable[foundation_events.Event]:
        yield from self.resource_uow.collect_new_events()
        yield from self.entry_repo_uow.collect_new_events()

    def get_entry_uow(self, entry_repo_id: unique_id.UniqueId) -> EntryUnitOfWork:
        with self.entry_repo_uow as uw:
            return uw.repo.get_by_id(entry_repo_id)


class AddingEntry(BasingEntry, CommandHandler[commands.AddEntry]):
    def execute(self, command: commands.AddEntry):
        with self.resource_uow:
            resource = self.resource_uow.repo.by_resource_id(command.resource_id)

        # try:
        #     entry_id = resource.id_getter()(command.entry)
        # except KeyError as err:
        #     raise errors.MissingIdField(
        #         resource_id=command.resource_id, entry=command.entry
        #     ) from err
        entry_schema = EntrySchema(resource.entry_json_schema)

        with self.get_entry_uow(resource.entry_repository_id) as uw:
            existing_entry = uw.repo.get_by_id_optional(command.entity_id)
            if (
                existing_entry
                and not existing_entry.discarded
                and existing_entry.entity_id != command.entity_id
            ):
                raise errors.IntegrityError(
                    f"An entry with entry_id '{command.entity_id}' already exists."
                )

            entry_schema.validate_entry(command.entry)

            entry = resource.create_entry_from_dict(
                command.entry,
                user=command.user,
                message=command.message,
                entity_id=command.entity_id,
                timestamp=command.timestamp,
            )
            uw.entries.save(entry)
            uw.commit()
        return entry


class UpdatingEntry(BasingEntry, CommandHandler[commands.UpdateEntry]):
    def execute(self, command: commands.UpdateEntry):
        with self.resource_uow:
            resource = self.resource_uow.repo.by_resource_id(command.resource_id)

        entry_schema = EntrySchema(resource.entry_json_schema)
        entry_schema.validate_entry(command.entry)

        with self.get_entry_uow(resource.entry_repository_id) as uw:
            try:
                current_db_entry = uw.repo.by_id(command.entity_id)
            except errors.EntryNotFound as err:
                raise errors.EntryNotFound(
                    command.resource_id,
                    entity_id=command.entity_id,
                ) from err

            diff = jsondiff.compare(current_db_entry.body, command.entry)
            if not diff:
                return current_db_entry

            #     db_entry_json = json.dumps(entry)
            #     db_id = current_db_entry.id
            #     latest_history_entry = (
            #         resource.history_model.query.filter_by(entry_id=db_id)
            #         .order_by(resource.history_model.version.desc())
            #         .first()
            #     )
            if not command.force and current_db_entry.version != command.version:
                logger.info(
                    "version conflict",
                    extra={
                        "current_version": current_db_entry.version,
                        "version": command.version,
                    },
                )
                raise errors.UpdateConflict(diff)

            # id_getter = resource.id_getter()
            # new_entry_id = id_getter(command.entry)
            current_db_entry.update_body(
                command.entry,
                user=command.user,
                message=command.message,
                timestamp=command.timestamp,
            )
            # current_db_entry.stamp(
            #     command.user, message=command.message, timestamp=command.timestamp
            # )
            # if new_entry_id != command.entry_id:
            #     logger.info(
            #         "updating entry_id",
            #         extra={
            #             "entry_id": command.entry_id,
            #             "new_entry_id": new_entry_id,
            #         },
            #     )
            #     current_db_entry.entry_id = new_entry_id
            #     # uw.repo.move(current_db_entry, old_entry_id=command.entry_id)
            #     uw.repo.save(current_db_entry)
            # else:
            uw.repo.save(current_db_entry)
            uw.commit()

        return current_db_entry


# def update_entries(*args, **kwargs):
#     return []


# def add_entries_from_file(
#     resource_id: str, version: int, filename: Path
# ) -> list[Entry]:
#     return add_entries(
#         resource_id,
#         json_streams.load_from_file(filename),
#         user_id="local_admin",
#         resource_version=version,
#     )


class AddingEntries(BasingEntry, CommandHandler[commands.AddEntries]):
    def execute(self, command: commands.AddEntries):
        """
        Add entries to DB and INDEX (if present and resource is active).

        Raises
        ------
        RuntimeError
            If the resource.entry_json_schema fails to compile.
        KarpError
            - If an entry fails to be validated against the json schema.
            - If the DB interaction fails.

        Returns
        -------
        List
            List of the id's of the created entries.
        """

        if not isinstance(command.resource_id, str):
            raise ValueError(
                f"'resource_id' must be of type 'str', were '{type(command.resource_id)}'"
            )
        with self.resource_uow:
            resource = self.resource_uow.resources.by_resource_id(command.resource_id)

        if not resource:
            raise errors.ResourceNotFound(command.resource_id)

        entry_schema = EntrySchema(resource.entry_json_schema)

        created_db_entries = []
        with self.entry_repo_uow, self.entry_repo_uow.repo.get_by_id(
            resource.entry_repository_id
        ) as uw:
            for i, entry_raw in enumerate(command.entries):

                entry_schema.validate_entry(entry_raw)

                entry = resource.create_entry_from_dict(
                    entry_raw,
                    user=command.user,
                    message=command.message,
                    entity_id=unique_id.make_unique_id(),
                )
                existing_entry = uw.repo.get_by_id_optional(entry.entity_id)
                if existing_entry and not existing_entry.discarded:
                    raise errors.IntegrityError(
                        f"An entry with entry_id '{entry.entity_id}' already exists."
                    )
                uw.entries.save(entry)
                created_db_entries.append(entry)

                if command.chunk_size > 0 and i % command.chunk_size == 0:
                    uw.commit()
            uw.commit()

        return created_db_entries


class ImportingEntries(BasingEntry, CommandHandler[commands.ImportEntries]):
    def execute(self, command: commands.ImportEntries):
        """
        Import entries to DB and INDEX (if present and resource is active).

        Raises
        ------
        RuntimeError
            If the resource.entry_json_schema fails to compile.
        KarpError
            - If an entry fails to be validated against the json schema.
            - If the DB interaction fails.

        Returns
        -------
        List
            List of the id's of the created entries.
        """

        if not isinstance(command.resource_id, str):
            raise ValueError(
                f"'resource_id' must be of type 'str', were '{type(command.resource_id)}'"
            )
        with self.resource_uow:
            resource = self.resource_uow.resources.by_resource_id(command.resource_id)

        if not resource:
            raise errors.ResourceNotFound(command.resource_id)

        entry_schema = EntrySchema(resource.entry_json_schema)

        created_db_entries = []
        with self.entry_repo_uow, self.entry_repo_uow.repo.get_by_id(
            resource.entry_repository_id
        ) as uw:
            for i, entry_raw in enumerate(command.entries):
                entry_schema.validate_entry(entry_raw["entry"])

                entry = resource.create_entry_from_dict(
                    entry_raw["entry"],
                    user=entry_raw.get("user") or command.user,
                    message=entry_raw.get("message") or command.message,
                    entity_id=entry_raw.get("entity_id") or unique_id.make_unique_id(),
                    timestamp=entry_raw.get("last_modified"),
                )
                # if entity_id := entry_raw.get("entity_id"):
                #     existing_entry = uw.repo.get_by_id_optional(entity_id)
                #     if existing_entry and not existing_entry.discarded:
                #         raise errors.IntegrityError(
                #             f"An entry with entry_id '{entry.entity_id}' already exists."
                #         )

                #             if entity_id != existing_entry.entity_id:
                #                 raise integrity_error
                #         else:
                #             raise integrity_error
                uw.entries.save(entry)
                created_db_entries.append(entry)

                if command.chunk_size > 0 and i % command.chunk_size == 0:
                    uw.commit()
            uw.commit()

        return created_db_entries


class DeletingEntry(BasingEntry, CommandHandler[commands.DeleteEntry]):
    def execute(self, command: commands.DeleteEntry):
        with self.resource_uow:
            resource = self.resource_uow.repo.by_resource_id(command.resource_id)

        with self.entry_repo_uow, self.entry_repo_uow.repo.get_by_id(
            resource.entry_repository_id
        ) as uw:
            entry = uw.repo.by_id(command.entity_id)

            entry.discard(
                user=command.user,
                message=command.message or "Entry deleted.",
                timestamp=command.timestamp,
            )
            uw.repo.save(entry)
            uw.commit()
