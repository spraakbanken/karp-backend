import collections
import json
import logging
import typing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generic, List, Optional, Tuple

import fastjsonschema  # pyre-ignore
import json_streams
from sb_json_tools import jsondiff
import logging

from karp.foundation.commands import CommandHandler
from karp.lex.application.repositories import EntryUnitOfWork
from karp.lex.domain import errors, entities
from karp.lex.domain.entities.entry import Entry
from karp.lex.domain.entities.resource import Resource
from karp.foundation.value_objects import unique_id
from karp.errors import (ClientErrorCodes, EntryIdMismatch, EntryNotFoundError,
                         KarpError, UpdateConflict)
from karp.foundation import events as foundation_events
from karp.foundation import messagebus
from karp.lex.domain import commands
from karp.lex.domain.value_objects import EntrySchema
from karp.lex.application import repositories


logger = logging.getLogger(__name__)


# def get_entries_by_column(resource_obj: Resource, filters):
#     config = resource_obj.config
#     cls = resource_obj.model
#     query = cls.query
#
#     joined_filters = []
#     simple_filters = {}
#
#     for filter_key in filters.keys():
#         tmp = collections.defaultdict(dict)
#         if filter_key in config["referenceable"] and config["fields"][filter_key].get(
#             "collection", False
#         ):
#             child_cls = cls.child_tables[filter_key]
#             tmp[child_cls.__tablename__][filter_key] = filters[filter_key]
#         else:
#             simple_filters[filter_key] = filters[filter_key]
#         joined_filters.extend(tmp.values())
#
#     query = query.filter_by(**simple_filters)
#
#     for child_filters in joined_filters:
#         child_cls = cls.child_tables[list(child_filters.keys())[0]]
#         query = query.join(child_cls).filter_by(**child_filters)
#
#     return [
#         {
#             "id": db_entry.id,
#             "entry_id": db_entry.entry_id,
#             "entry": json.loads(db_entry.body),
#         }
#         for db_entry in query
#     ]
#
#
# def get_entry(resource_id: str, entry_id: str, version: Optional[int] = None):
#     resource = get_resource(resource_id, version=version)
#     return get_entry_by_entry_id(resource, entry_id)
#
#
# def get_entry_by_entry_id(resource: Resource, entry_id: str):
#     cls = resource.model
#     return cls.query.filter_by(entry_id=entry_id).first()
#
#
class BasingEntry:
    def __init__(
        self,
        entry_repo_uow: repositories.EntryUowRepositoryUnitOfWork,
        resource_uow: repositories.ResourceUnitOfWork
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

    def execute(self, cmd: commands.AddEntry):
        with self.resource_uow:
            resource = self.resource_uow.repo.by_resource_id(
                cmd.resource_id)

        try:
            entry_id = resource.id_getter()(cmd.entry)
        except KeyError as err:
            raise errors.MissingIdField(
                resource_id=cmd.resource_id,
                entry=cmd.entry
            ) from err
        entry_schema = EntrySchema(resource.entry_json_schema)

        with self.get_entry_uow(resource.entry_repository_id) as uw:
            existing_entry = uw.repo.get_by_entry_id_optional(entry_id)
            if (
                existing_entry
                and not existing_entry.discarded
                and existing_entry.entity_id != cmd.entity_id
            ):
                raise errors.IntegrityError(
                    f"An entry with entry_id '{entry_id}' already exists."
                )

            entry_schema.validate_entry(cmd.entry)

            entry = resource.create_entry_from_dict(
                cmd.entry,
                user=cmd.user,
                message=cmd.message,
                entity_id=cmd.entity_id
            )
            uw.entries.save(entry)
            uw.commit()
        return entry


#
# def preview_entry(resource_id, entry, resource_version=None):
#     resource = get_resource(resource_id, version=resource_version)
#     entry_json = _validate_and_prepare_entry(resource, entry)
#     return entry_json


class UpdatingEntry(BasingEntry, CommandHandler[commands.UpdateEntry]):
    def execute(self, cmd: commands.UpdateEntry):
        with self.resource_uow:
            resource = self.resource_uow.repo.by_resource_id(
                cmd.resource_id
            )

        entry_schema = EntrySchema(resource.entry_json_schema)
        entry_schema.validate_entry(cmd.entry)

        with self.get_entry_uow(resource.entry_repository_id) as uw:
            try:
                current_db_entry = uw.repo.by_entry_id(
                    cmd.entry_id
                )
            except errors.EntryNotFound as err:
                raise errors.EntryNotFound(
                    cmd.resource_id,
                    cmd.entry_id,
                    entity_id=None,
                ) from err

            diff = jsondiff.compare(current_db_entry.body, cmd.entry)
            if not diff:
                return current_db_entry

            #     db_entry_json = json.dumps(entry)
            #     db_id = current_db_entry.id
            #     latest_history_entry = (
            #         resource.history_model.query.filter_by(entry_id=db_id)
            #         .order_by(resource.history_model.version.desc())
            #         .first()
            #     )
            if not cmd.force and current_db_entry.version != cmd.version:
                logger.info(
                    'version conflict', current_version=current_db_entry.version, version=cmd.version)
                raise errors.UpdateConflict(diff)

            id_getter = resource.id_getter()
            new_entry_id = id_getter(cmd.entry)

            current_db_entry.body = cmd.entry
            current_db_entry.stamp(
                cmd.user, message=cmd.message, timestamp=cmd.timestamp)
            if new_entry_id != cmd.entry_id:
                logger.info('updating entry_id',
                            entry_id=cmd.entry_id, new_entry_id=new_entry_id)
                current_db_entry.entry_id = new_entry_id
                # uw.repo.move(current_db_entry, old_entry_id=cmd.entry_id)
                uw.repo.save(current_db_entry)
            else:
                uw.repo.save(current_db_entry)
            uw.commit()

        return current_db_entry


def update_entries(*args, **kwargs):
    return []


def add_entries_from_file(
    resource_id: str, version: int, filename: Path
) -> List[Entry]:
    return add_entries(
        resource_id,
        json_streams.load_from_file(filename),
        user_id="local_admin",
        resource_version=version,
    )


class AddingEntries(
    BasingEntry,
    CommandHandler[commands.AddEntries]
):
    def execute(self, cmd: commands.AddEntries):
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

        if not isinstance(cmd.resource_id, str):
            raise ValueError(
                f"'resource_id' must be of type 'str', were '{type(cmd.resource_id)}'"
            )
        with self.resource_uow:
            resource = self.resource_uow.resources.by_resource_id(
                cmd.resource_id)

        if not resource:
            raise errors.ResourceNotFound(cmd.resource_id)

        entry_schema = EntrySchema(resource.entry_json_schema)

        created_db_entries = []
        with self.entry_repo_uow, self.entry_repo_uow.repo.get_by_id(
                resource.entry_repository_id) as uw:
            for entry_raw in cmd.entries:
                entry_schema.validate_entry(entry_raw)

                entry = resource.create_entry_from_dict(
                    entry_raw,
                    user=cmd.user,
                    message=cmd.message,
                    entity_id=unique_id.make_unique_id(),
                )
                uw.entries.save(entry)
                created_db_entries.append(entry)
            uw.commit()

        return created_db_entries


# def add_entries(
#     resource_id: str,
#     entries: List[Dict],
#     user_id: str,
#     message: str = None,
#     resource_version: int = None,
# ):
#     """
#     Add entries to DB and INDEX (if present and resource is active).
#
#     Raises
#     ------
#     RuntimeError
#         If the resource.entry_json_schema fails to compile.
#     KarpError
#         - If an entry fails to be validated against the json schema.
#         - If the DB interaction fails.
#
#     Returns
#     -------
#     List
#         List of the id's of the created entries.
#     """
#     resource = get_resource(resource_id, version=resource_version)
#     resource_conf = resource.config
#
#     validate_entry = _compile_schema(resource.entry_json_schema)
#
#     try:
#         created_db_entries = []
#         for entry in entries:
#             _validate_entry(validate_entry, entry)
#
#             entry_json = json.dumps(entry)
#             db_entry = _src_entry_to_db_entry(
#                 entry, entry_json, resource.model, resource_conf
#             )
#             created_db_entries.append((db_entry, entry, entry_json))
#             db.session.add(db_entry)
#
#         db.session.commit()
#
#         created_history_entries = []
#         for db_entry, entry, entry_json in created_db_entries:
#             history_entry = resource.history_model(
#                 entry_id=db_entry.id,
#                 user_id=user_id,
#                 body=entry_json,
#                 version=1,
#                 op="ADD",
#                 message=message,
#                 timestamp=datetime.now(timezone.utc).timestamp(),
#             )
#             created_history_entries.append((db_entry, entry, history_entry))
#             db.session.add(history_entry)
#         db.session.commit()
#     except sql_exception.IntegrityError as e:
#         _logger.exception("IntegrityError")
#         print("e = {e!r}".format(e=e))
#         print("e.orig.args = {e!r}".format(e=e.orig.args))
#         raise KarpError(
#             "Database error: {msg}".format(msg=e.orig.args),
#             ClientErrorCodes.DB_INTEGRITY_ERROR,
#         )
#     except sql_exception.SQLAlchemyError as e:
#         _logger.exception("Adding entries to DB failed.")
#         print("e = {e!r}".format(e=e))
#         raise KarpError(
#             "Database error: {msg}".format(msg=e.msg), ClientErrorCodes.DB_GENERAL_ERROR
#         )
#
#     if resource.active:
#         indexmgr.add_entries(
#             resource_id,
#             [
#                 (
#                     db_entry.entry_id,
#                     entrymetadata.EntryMetadata.init_from_model(history_entry),
#                     _src_entry_to_index_entry(resource, entry),
#                 )
#                 for db_entry, entry, history_entry in created_history_entries
#             ],
#         )
#
#     return [db_entry.entry_id for db_entry, _, _ in created_db_entries]
#
#
# def _src_entry_to_db_entry(entry, entry_json, resource_model, resource_conf):
#     kwargs = _src_entry_to_db_kwargs(entry, entry_json, resource_model, resource_conf)
#     db_entry = resource_model(**kwargs)
#     return db_entry
#
#
# def _src_entry_to_db_kwargs(entry, entry_json, resource_model, resource_conf):
#     kwargs = {"body": entry_json}
#
#     for field_name in resource_conf.get("referenceable", ()):
#         field_val = entry.get(field_name)
#         if resource_conf["fields"][field_name].get("collection", False):
#             child_table = resource_model.child_tables[field_name]
#             for elem in field_val:
#                 if field_name not in kwargs:
#                     kwargs[field_name] = []
#                 kwargs[field_name].append(child_table(**{field_name: elem}))
#         else:
#             if field_val:
#                 kwargs[field_name] = field_val
#     id_field = resource_conf.get("id")
#     if id_field:
#         kwargs["entry_id"] = entry[id_field]
#     else:
#         kwargs["entry_id"] = "TODO"  # generate id for resources that are missing it
#     return kwargs


class DeletingEntry(BasingEntry, CommandHandler[commands.DeleteEntry]):

    def execute(self, cmd: commands.DeleteEntry):
        with self.resource_uow:
            resource = self.resource_uow.repo.by_resource_id(cmd.resource_id)

        with self.entry_repo_uow, self.entry_repo_uow.repo.get_by_id(
            resource.entry_repository_id
        ) as uw:
            entry = uw.repo.by_entry_id(cmd.entry_id)

            entry.discard(
                user=cmd.user,
                message=cmd.message,
                timestamp=cmd.timestamp,
            )
            uw.repo.save(entry)
            uw.commit()

    # ctx.search_service.delete_entry(resource, entry=entry)


# def delete_entry(resource_id: str, entry_id: str, user_id: str):
#     resource = get_resource(resource_id)
#     entry = resource.model.query.filter_by(entry_id=entry_id, deleted=False).first()
#     if not entry:
#         raise EntryNotFoundError(resource_id, entry_id)
#     entry.deleted = True
#     history_cls = resource.history_model
#     history_entry = history_cls(
#         entry_id=entry.id,
#         user_id=user_id,
#         op="DELETE",
#         version=-1,
#         timestamp=datetime.now(timezone.utc).timestamp(),
#     )
#     db.session.add(history_entry)
#     db.session.commit()
#     indexmgr.delete_entry(resource_id, entry.entry_id)
#
#
def _src_entry_to_index_entry(resource: Resource, src_entry: Entry) -> Dict:
    return indexing.transform_to_index_entry(
        ctx.resource_repo, ctx.search_service, resource, src_entry
    )


# def _src_entry_to_index_entry(resource: Resource, src_entry: Dict):
#     """
#     Make a "src entry" into an "index entry"
#     """
#     return indexmgr.transform_to_index_entry(
#         resource, src_entry, resource.config["fields"].items()
#     )
#
#
# def _validate_and_prepare_entry(resource, entry):
#     validate_entry = _compile_schema(resource.entry_json_schema)
#     _validate_entry(validate_entry, entry)
#     return _src_entry_to_index_entry(resource, entry)
