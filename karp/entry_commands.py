from collections import defaultdict
from typing import Any, Dict, Generator, Iterable, List, Tuple

import sqlalchemy
from injector import inject
from sqlalchemy.orm import Session

from karp import plugins
from karp.foundation.timings import utc_now
from karp.foundation.value_objects import UniqueId, unique_id
from karp.lex import EntryDto
from karp.lex.domain import errors
from karp.lex.domain.entities import Resource
from karp.lex.domain.errors import EntryNotFound, ResourceNotFound
from karp.lex.infrastructure import EntryRepository, ResourceRepository
from karp.plugins import Plugins
from karp.search.domain.index_entry import IndexEntry
from karp.search.infrastructure.es.indices import EsIndex
from karp.search.infrastructure.transformers import entry_transformer


class EntryCommands:
    @inject
    def __init__(
        self,
        session: Session,
        resources: ResourceRepository,
        index: EsIndex,
        plugins: Plugins,
    ):
        self.session = session
        self.resources: ResourceRepository = resources
        self.index = index
        self.plugins = plugins
        self.added_entries = defaultdict(list)
        self.deleted_entries = defaultdict(list)
        self.in_transaction = False

    def _get_resource(self, resource_id: str) -> Resource:
        result = self.resources.by_resource_id(resource_id)
        if not result:
            raise ResourceNotFound(resource_id)
        return result

    def _get_entries(self, resource_id: str) -> EntryRepository:
        result = self.resources.entries_by_resource_id(resource_id)
        if not result:
            raise ResourceNotFound(resource_id)
        return result

    def _transform(self, config, entry: EntryDto) -> IndexEntry:
        return next(self._transform_entries(config, [entry]))

    def _transform_entries(self, config, entries: Iterable[EntryDto]) -> Generator[IndexEntry, Any, None]:
        config = plugins.transform_config(self.plugins, config)
        entries = plugins.transform_entries(self.plugins, config, entries)
        return (entry_transformer.transform(entry) for entry in entries)

    def add_entries_in_chunks(
        self,
        resource_id: str,
        chunk_size: int,
        entries: Iterable[Tuple[UniqueId, Dict]],
        user: str,
        message: str,
        timestamp: float | None = None,
    ) -> list[EntryDto]:
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
        """

        created_db_entries = []
        resource = self._get_resource(resource_id)

        entry_table = self._get_entries(resource_id)
        for i, (entry_id, entry_raw) in enumerate(entries):
            entry = resource.create_entry_from_dict(
                entry_raw,
                user=user,
                message=message,
                id=entry_id,
                timestamp=timestamp,
            )
            entry_table.save(entry)
            created_db_entries.append(EntryDto.from_entry(entry))

            if chunk_size > 0 and i % chunk_size == 0:
                self.added_entries[resource_id].extend(created_db_entries)
                self._commit()

        self.added_entries[resource_id].extend(created_db_entries)
        self._commit()

        return created_db_entries

    def add_entries(
        self,
        resource_id: str,
        entries: Iterable[Tuple[UniqueId, Dict]],
        user: str,
        message: str,
        timestamp: float | None = None,
    ):
        return self.add_entries_in_chunks(resource_id, 0, entries, user, message, timestamp=timestamp)

    def import_entries(self, resource_id, entries, user, message):
        return self.import_entries_in_chunks(resource_id, 0, entries, user, message)

    def import_entries_in_chunks(self, resource_id, chunk_size, entries, user, message):
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
        """

        created_db_entries = []
        resource = self._get_resource(resource_id)
        entry_table = self._get_entries(resource_id)

        for i, entry_raw in enumerate(entries):
            entry = resource.create_entry_from_dict(
                entry_raw["entry"],
                user=entry_raw.get("user") or user,
                message=entry_raw.get("message") or message,
                id=entry_raw.get("id") or unique_id.make_unique_id(),
                timestamp=entry_raw.get("last_modified"),
            )
            entry_table.save(entry)

            created_db_entries.append(EntryDto.from_entry(entry))

            if chunk_size > 0 and i % chunk_size == 0:
                self.added_entries[resource_id].extend(created_db_entries)
                self._commit()

        self.added_entries[resource_id].extend(created_db_entries)
        self._commit()

        return created_db_entries

    def add_entry(self, resource_id, entry_id, entry, user, message, timestamp=None):
        result = self.add_entries(resource_id, [(entry_id, entry)], user, message, timestamp=timestamp)
        assert len(result) == 1  # noqa: S101
        return result[0]

    def update_entry(self, resource_id, _id, version, user, message, entry, timestamp=None):
        resource = self._get_resource(resource_id)
        entries = self._get_entries(resource_id)
        try:
            current_db_entry = entries.by_id(_id)
        except EntryNotFound as err:
            raise EntryNotFound(
                resource_id,
                id=_id,
            ) from err

        resource.update_entry(
            entry=current_db_entry,
            body=entry,
            version=version,
            user=user,
            message=message,
            timestamp=timestamp or utc_now(),
        )
        if version != current_db_entry.version:
            entries.save(current_db_entry)
            self.added_entries[resource_id].append(EntryDto.from_entry(current_db_entry))
            self._commit()

        return EntryDto.from_entry(current_db_entry)

    def delete_entry(self, resource_id, _id, user, version, message="Entry deleted", timestamp=None):
        resource = self._get_resource(resource_id)
        entries = self._get_entries(resource_id)
        entry = entries.by_id(_id)

        resource.discard_entry(
            entry=entry,
            version=version,
            user=user,
            message=message,
            timestamp=timestamp or utc_now(),
        )
        entries.save(entry)
        self.deleted_entries[resource_id].append(entry.id)
        self._commit()

    def _commit(self):
        """Commits the session and updates ES, but not if in a transaction."""

        if self.in_transaction:
            return

        try:
            self.session.commit()
        except sqlalchemy.exc.IntegrityError as e:
            self.session.rollback()
            raise errors.IntegrityError(str(e)) from None

        for resource_id, entry_dtos in self.added_entries.items():
            resource = self._get_resource(resource_id)
            index_entries = self._transform_entries(resource.config, entry_dtos)
            self.index.add_entries(resource.resource_id, index_entries)
        self.added_entries.clear()

        for resource_id, entry_ids in self.deleted_entries.items():
            self.index.delete_entries(resource_id, entry_ids=entry_ids)
        self.deleted_entries.clear()

    def start_transaction(self):
        """Runs commands inside a transaction. Nothing will be
        committed until the transaction ends."""

        if self.in_transaction:
            raise RuntimeError("Nested transactions are not supported")

        self.in_transaction = True

    def commit(self):
        """Commits a transaction."""

        if not self.in_transaction:
            raise RuntimeError("Can't commit when outside a transaction")

        self.in_transaction = False
        self._commit()

    def rollback(self):
        """Aborts a transaction."""

        if not self.in_transaction:
            raise RuntimeError("Can't roll back when outside a transaction")

        self.in_transaction = True
        self.added_entries.clear()
        self.deleted_entries.clear()
