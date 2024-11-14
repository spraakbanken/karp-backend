from typing import Dict, Iterable, Tuple

import sqlalchemy
from injector import inject
from sqlalchemy.orm import Session

from karp.foundation.timings import utc_now
from karp.foundation.value_objects import UniqueId, unique_id
from karp.lex import EntryDto
from karp.lex.domain import errors
from karp.lex.domain.entities import Resource
from karp.lex.domain.errors import EntryNotFound, ResourceNotFound
from karp.lex.infrastructure import EntryRepository, ResourceRepository


class EntryCommands:
    @inject
    def __init__(
        self,
        session: Session,
        resources: ResourceRepository,
    ):
        self.session = session
        self.resources: ResourceRepository = resources
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

    def add_entries_in_chunks(
        self,
        resource_id: str,
        chunk_size: int,
        entries: Iterable[Tuple[UniqueId, Dict]],
        user: str,
        message: str,
        timestamp: float | None = None,
    ):
        """
        Add entries to DB and INDEX (if present and resource is active).

        Raises
        ------
        RuntimeError
            If the resource.entry_schema fails to compile.
        KarpError
            - If an entry fails to be validated against the json schema.
            - If the DB interaction fails.
        """
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
            if chunk_size > 0 and i % chunk_size == 0:
                self._commit()
        self._commit()

    def add_entries(
        self,
        resource_id: str,
        entries: Iterable[Tuple[UniqueId, Dict]],
        user: str,
        message: str,
        timestamp: float | None = None,
    ):
        self.add_entries_in_chunks(resource_id, 0, entries, user, message, timestamp=timestamp)

    def import_entries(self, resource_id, entries, user, message):
        self.import_entries_in_chunks(resource_id, 0, entries, user, message)

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
        """
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

            if chunk_size > 0 and i % chunk_size == 0:
                self._commit()
        self._commit()

    def add_entry(self, resource_id, entry_id, entry, user, message, timestamp=None):
        self.add_entries(resource_id, [(entry_id, entry)], user, message, timestamp=timestamp)

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
        self._commit()

    def _commit(self):
        """Commits the session, but not if in a transaction."""

        if self.in_transaction:
            return
        try:
            self.session.commit()
        except sqlalchemy.exc.IntegrityError as e:
            self.session.rollback()
            raise errors.IntegrityError(str(e)) from None

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
