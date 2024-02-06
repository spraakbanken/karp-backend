import logging
import typing

from karp.lex.application.dtos import ResourceDto
from karp.lex.application.queries import (
    EntryDto,
)
from karp.lex.domain import errors as lex_errors
from karp.lex_infrastructure import SqlReadOnlyResourceRepository
from karp.search.application.repositories.indicies import IndexEntry
from karp.search_infrastructure.repositories.es6_indicies import Es6Index

logger = logging.getLogger(__name__)


class GenericEntryTransformer:
    def __init__(
        self,
        index: Es6Index,
        resource_repo: SqlReadOnlyResourceRepository,
    ) -> None:
        super().__init__()
        self.index = index
        self.resource_repo = resource_repo

    def transform(self, resource_id: str, src_entry: EntryDto) -> IndexEntry:
        logger.debug(
            "transforming entry",
            extra={"entity_id": src_entry.id, "resource_id": resource_id},
        )
        index_entry = self.index.create_empty_object()
        index_entry.id = str(src_entry.id)
        self.index.assign_field(index_entry, "_entry_version", src_entry.version)
        self.index.assign_field(index_entry, "_last_modified", src_entry.last_modified)
        self.index.assign_field(index_entry, "_last_modified_by", src_entry.last_modified_by)
        resource = self.resource_repo.by_resource_id_optional(resource_id)
        if not resource:
            raise lex_errors.ResourceNotFound(None, resource_id=resource_id)
        self._transform_to_index_entry(
            src_entry.entry,
            index_entry,
            resource.config["fields"].items(),
        )
        logger.debug("transformed entry", extra={"entry": src_entry, "index_entry": index_entry})
        return index_entry

    def _transform_to_index_entry(
        self,
        _src_entry: typing.Dict,
        _index_entry: IndexEntry,
        fields,
    ):
        logger.debug("transforming [part of] entry", extra={"src_entry": _src_entry})
        for field_name, field_conf in fields:
            field_content = None

            if field_conf.get("collection"):
                field_content = []
                if field_name in _src_entry:
                    for subfield in _src_entry[field_name]:
                        if field_conf["type"] == "object":
                            subfield_content = self.index.create_empty_object()
                            self._transform_to_index_entry(
                                subfield,
                                subfield_content,
                                field_conf["fields"].items(),
                            )
                            self.index.add_to_list_field(field_content, subfield_content.entry)
                        else:
                            self.index.add_to_list_field(field_content, subfield)
                    self.index.assign_field(_index_entry, field_name, field_content)

            elif field_conf["type"] == "object":
                field_content = self.index.create_empty_object()
                if field_name in _src_entry:
                    self._transform_to_index_entry(
                        _src_entry[field_name],
                        field_content,
                        field_conf["fields"].items(),
                    )
                    self.index.assign_field(_index_entry, field_name, field_content)

            elif field_conf["type"] in (
                "integer",
                "string",
                "number",
                "boolean",
                "long_string",
            ):
                if field_name in _src_entry:
                    field_content = _src_entry[field_name]
                    self.index.assign_field(_index_entry, field_name, field_content)
