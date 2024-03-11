from injector import inject
from sqlalchemy.orm import Session

from karp import plugins
from karp.foundation.timings import utc_now
from karp.foundation.value_objects import unique_id
from karp.lex import EntryDto
from karp.lex.domain.entities import Resource
from karp.lex.domain.errors import EntryNotFound, ResourceNotFound
from karp.lex.infrastructure import EntryRepository, ResourceRepository
from karp.plugins import Plugins
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

    def _get_resource(self, resource_id: unique_id.UniqueId) -> Resource:
        if not isinstance(resource_id, str):
            raise ValueError(f"'resource_id' must be of type 'str', were '{type(resource_id)}'")

        result = self.resources.by_resource_id(resource_id)
        if not result:
            raise ResourceNotFound(resource_id)
        return result

    def _get_entries(self, resource_id: unique_id.UniqueId) -> EntryRepository:
        result = self.resources.entries_by_resource_id(resource_id)
        if not result:
            raise ResourceNotFound(resource_id)
        return result

    def _transform(self, resource, entry):
        config = plugins.transform_config(self.plugins, resource.config)
        entry = entry.copy()
        entry.entry = plugins.transform(self.plugins, config, entry.entry)
        return entry_transformer.transform(config, entry)

    def add_entries_in_chunks(self, resource_id, chunk_size, entries, user, message):
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
        for i, entry_raw in enumerate(entries):
            entry = resource.create_entry_from_dict(
                entry_raw,
                user=user,
                message=message,
                id=unique_id.make_unique_id(),
            )
            entry_table.save(entry)
            created_db_entries.append(EntryDto.from_entry(entry))

            if chunk_size > 0 and i % chunk_size == 0:
                self.session.commit()
        self.session.commit()
        self._entry_added_handler(resource, created_db_entries)

        return created_db_entries

    def add_entries(self, resource_id, entries, user, message):
        return self.add_entries_in_chunks(resource_id, 0, entries, user, message)

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
                self.session.commit()
        self.session.commit()
        self._entry_added_handler(resource, created_db_entries)

        return created_db_entries

    def add_entry(self, resource_id, entry, user, message):
        result = self.add_entries(resource_id, [entry], user, message)
        assert len(result) == 1  # noqa: S101
        return result[0]

    def update_entry(self, resource_id, _id, version, user, message, entry):
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
            timestamp=utc_now(),
        )
        if version != current_db_entry.version:
            entries.save(current_db_entry)
            self.session.commit()
            self._entry_updated_handler(resource, EntryDto.from_entry(current_db_entry))

        return EntryDto.from_entry(current_db_entry)

    def delete_entry(self, resource_id, _id, user, version, message="Entry deleted"):
        resource = self._get_resource(resource_id)
        entries = self._get_entries(resource_id)
        entry = entries.by_id(_id)

        resource.discard_entry(
            entry=entry,
            version=version,
            user=user,
            message=message,
            timestamp=utc_now(),
        )
        entries.save(entry)
        self.session.commit()
        self._entry_deleted_handler(EntryDto.from_entry(entry))

    def _entry_added_handler(self, resource, entry_dtos):
        entry_dtos = [self._transform(resource, entry_dto) for entry_dto in entry_dtos]
        self.index.add_entries(resource.resource_id, entry_dtos)

    def _entry_updated_handler(self, resource, entry_dto):
        self.index.add_entries(
            entry_dto.resource,
            [self._transform(resource, entry_dto)],
        )

    def _entry_deleted_handler(self, entry_dto):
        self.index.delete_entry(entry_dto.resource, entry_id=entry_dto.id)
