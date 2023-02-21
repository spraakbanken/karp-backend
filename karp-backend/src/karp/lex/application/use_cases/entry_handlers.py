import logging  # noqa: D100, I001
import typing  # noqa: F401

from sb_json_tools import jsondiff

from karp.command_bus import CommandHandler
from karp.lex.application.repositories import EntryUnitOfWork
from karp.lex.domain import errors
from karp.lex_core.value_objects import unique_id

from karp.foundation import events as foundation_events  # noqa: F401
from karp.lex_core import commands
from karp.lex.domain.value_objects import EntrySchema
from karp.lex.application import repositories


logger = logging.getLogger(__name__)


class BasingEntry:  # noqa: D101
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


class AddingEntry(BasingEntry, CommandHandler[commands.AddEntry]):  # noqa: D101
    def execute(self, command: commands.AddEntry):  # noqa: ANN201, D102
        with self.resource_uow:
            resource = self.resource_uow.repo.by_resource_id(command.resource_id)

        # try:
        #     entry_id = resource.id_getter()(command.entry)
        # except KeyError as err:
        #     raise errors.MissingIdField(
        #         resource_id=command.resource_id, entry=command.entry
        #     ) from err
        entry_schema = EntrySchema(resource.entry_json_schema)

        entry_uow = self.get_entry_uow(resource.entry_repository_id)
        with entry_uow as uw:
            existing_entry = uw.repo.get_by_id_optional(command.id)
            if (
                existing_entry
                and not existing_entry.discarded
                and existing_entry.id != command.id
            ):
                raise errors.IntegrityError(
                    f"An entry with entry_id '{command.id}' already exists."
                )

            entry_schema.validate_entry(command.entry)

            entry, events = resource.create_entry_from_dict(
                command.entry,
                user=command.user,
                message=command.message,
                id=command.id,
                timestamp=command.timestamp,
            )
            uw.entries.save(entry)
            uw.post_on_commit(events)
            uw.commit()
        return entry


class UpdatingEntry(BasingEntry, CommandHandler[commands.UpdateEntry]):  # noqa: D101
    def execute(self, command: commands.UpdateEntry):  # noqa: ANN201, D102
        with self.resource_uow:
            resource = self.resource_uow.repo.by_resource_id(command.resource_id)

        entry_schema = EntrySchema(resource.entry_json_schema)
        entry_schema.validate_entry(command.entry)

        with self.get_entry_uow(resource.entry_repository_id) as uw:
            try:
                current_db_entry = uw.repo.by_id(command.id)
            except errors.EntryNotFound as err:
                raise errors.EntryNotFound(
                    command.resource_id,
                    id=command.id,
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
            events = current_db_entry.update_body(
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
            uw.post_on_commit(events)
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


class AddingEntries(BasingEntry, CommandHandler[commands.AddEntries]):  # noqa: D101
    def execute(self, command: commands.AddEntries):  # noqa: ANN201
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
        """  # noqa: D202, D212

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

                entry, events = resource.create_entry_from_dict(
                    entry_raw,
                    user=command.user,
                    message=command.message,
                    id=unique_id.make_unique_id(),
                )
                existing_entry = uw.repo.get_by_id_optional(entry.id)
                if existing_entry and not existing_entry.discarded:
                    raise errors.IntegrityError(
                        f"An entry with entry_id '{entry.id}' already exists."
                    )
                uw.entries.save(entry)
                created_db_entries.append(entry)

                uw.post_on_commit(events)
                if command.chunk_size > 0 and i % command.chunk_size == 0:
                    uw.commit()
            uw.commit()

        return created_db_entries


class ImportingEntries(  # noqa: D101
    BasingEntry, CommandHandler[commands.ImportEntries]
):
    def execute(self, command: commands.ImportEntries):  # noqa: ANN201
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
        """  # noqa: D202, D212

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

                entry, events = resource.create_entry_from_dict(
                    entry_raw["entry"],
                    user=entry_raw.get("user") or command.user,
                    message=entry_raw.get("message") or command.message,
                    id=entry_raw.get("id") or unique_id.make_unique_id(),
                    timestamp=entry_raw.get("last_modified"),
                )
                # if id := entry_raw.get("id"):
                #     existing_entry = uw.repo.get_by_id_optional(id)
                #     if existing_entry and not existing_entry.discarded:
                #         raise errors.IntegrityError(
                #             f"An entry with entry_id '{entry.id}' already exists."
                #         )

                #             if id != existing_entry.id:
                #                 raise integrity_error
                #         else:
                #             raise integrity_error
                uw.entries.save(entry)
                uw.post_on_commit(events)
                created_db_entries.append(entry)

                if command.chunk_size > 0 and i % command.chunk_size == 0:
                    uw.commit()
            uw.commit()

        return created_db_entries


class DeletingEntry(BasingEntry, CommandHandler[commands.DeleteEntry]):  # noqa: D101
    def execute(self, command: commands.DeleteEntry):  # noqa: ANN201, D102
        with self.resource_uow:
            resource = self.resource_uow.repo.by_resource_id(command.resource_id)

        with self.entry_repo_uow, self.entry_repo_uow.repo.get_by_id(
            resource.entry_repository_id
        ) as uw:
            entry = uw.repo.by_id(command.id)

            events = entry.discard(
                user=command.user,
                message=command.message or "Entry deleted.",
                timestamp=command.timestamp,
            )
            uw.repo.save(entry)
            uw.post_on_commit(events)
            uw.commit()
