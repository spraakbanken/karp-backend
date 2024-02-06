from karp.lex import EntryDto
from karp.lex.application.repositories import EntryRepository, ResourceRepository
from karp.lex.domain.entities import Resource
from karp.lex.domain.errors import EntryNotFound, ResourceNotFound
from karp.lex_core.value_objects import unique_id
from karp.search.generic_resources import GenericResourceViews
from karp.search_infrastructure import GenericEntryTransformer
from karp.search_infrastructure.repositories.es6_indicies import Es6Index
from karp.timings import utc_now


class EntryCommands:
    def __init__(
        self,
        session,
        resources: ResourceRepository,
        index: Es6Index,
        entry_transformer: GenericEntryTransformer,
    ):
        self.session = session
        self.resources: ResourceRepository = resources
        self.index = index
        self.entry_transformer = entry_transformer

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
            created_db_entries.append(entry)

            if chunk_size > 0 and i % chunk_size == 0:
                self.session.commit()
        self.session.commit()
        self._entry_added_handler(created_db_entries)

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
        """  # noqa: D202, D212

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

            created_db_entries.append(entry)

            if chunk_size > 0 and i % chunk_size == 0:
                self.session.commit()
        self.session.commit()
        self._entry_added_handler(created_db_entries)

        return created_db_entries

    def add_entry(self, resource_id, user, message, entry):
        resource = self._get_resource(resource_id)
        entries = self._get_entries(resource_id)
        entry = resource.create_entry_from_dict(
            entry,
            user=user,
            message=message,
            id=unique_id.make_unique_id(),
            timestamp=utc_now(),
        )
        entries.save(entry)
        self.session.commit()
        self._entry_added_handler([entry])
        return entry

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
            self._entry_updated_handler(current_db_entry)

        return current_db_entry

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
        self._entry_deleted_handler(entry)

    def _entry_added_handler(self, entries):
        entry_dtos = []
        for entry in entries:
            entry_dto = EntryDto(
                id=entry.id,
                resource=entry.resource_id,
                entry=entry.body,
                message=entry.message or "",
                lastModified=entry.last_modified,
                lastModifiedBy=entry.last_modified_by,
                version=1,
            )
            entry_dtos.append(self.entry_transformer.transform(entry.resource_id, entry_dto))
        self.index.add_entries(entry.resource_id, entry_dtos)

    def _entry_updated_handler(self, entry):
        entry_dto = EntryDto(
            id=entry.id,
            resource=entry.resource_id,
            entry=entry.body,
            message=entry.message,
            lastModified=entry.last_modified,
            lastModifiedBy=entry.last_modified_by,
            version=entry.version,
        )
        self.index.add_entries(
            entry.resource_id,
            [self.entry_transformer.transform(entry.resource_id, entry_dto)],
        )

    def _entry_deleted_handler(self, entry):
        self.index.delete_entry(entry.resource_id, entry_id=entry.id)
