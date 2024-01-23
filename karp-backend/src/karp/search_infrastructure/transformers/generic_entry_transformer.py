import logging
import typing

from karp.lex.application.dtos import ResourceDto
from karp.lex.application.queries import (
    EntryDto,
)
from karp.lex.domain import errors as lex_errors
from karp.lex_infrastructure import GenericEntryViews, SqlReadOnlyResourceRepository
from karp.search.application.repositories.indicies import IndexEntry, IndexUnitOfWork

logger = logging.getLogger(__name__)


class GenericEntryTransformer:
    def __init__(  # noqa: D107
        self,
        index_uow: IndexUnitOfWork,
        resource_repo: SqlReadOnlyResourceRepository,
        entry_views: GenericEntryViews,
    ) -> None:
        super().__init__()
        self.index_uow = index_uow
        self.resource_repo = resource_repo
        self.entry_views = entry_views

    def transform(self, resource_id: str, src_entry: EntryDto) -> IndexEntry:
        logger.debug(
            "transforming entry",
            extra={"entity_id": src_entry.id, "resource_id": resource_id},
        )
        index_entry = self.index_uow.repo.create_empty_object()
        index_entry.id = str(src_entry.id)
        self.index_uow.repo.assign_field(
            index_entry, "_entry_version", src_entry.version
        )
        self.index_uow.repo.assign_field(
            index_entry, "_last_modified", src_entry.last_modified
        )
        self.index_uow.repo.assign_field(
            index_entry, "_last_modified_by", src_entry.last_modified_by
        )
        resource = self.resource_repo.get_by_resource_id(resource_id)
        if not resource:
            raise lex_errors.ResourceNotFound(None, resource_id=resource_id)
        self._transform_to_index_entry(
            resource,
            # resource_repo,
            # indexer,
            src_entry.entry,
            index_entry,
            resource.config["fields"].items(),
        )
        logger.debug(
            "transformed entry", extra={"entry": src_entry, "index_entry": index_entry}
        )
        return index_entry

    def _transform_to_index_entry(  # noqa: ANN202, C901
        self,
        resource: ResourceDto,
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
                            subfield_content = self.index_uow.repo.create_empty_object()
                            self._transform_to_index_entry(
                                resource,
                                subfield,
                                subfield_content,
                                field_conf["fields"].items(),
                            )
                            self.index_uow.repo.add_to_list_field(
                                field_content, subfield_content.entry
                            )
                        else:
                            self.index_uow.repo.add_to_list_field(
                                field_content, subfield
                            )
                    self.index_uow.repo.assign_field(
                        _index_entry, field_name, field_content
                    )

            elif field_conf["type"] == "object":
                field_content = self.index_uow.repo.create_empty_object()
                if field_name in _src_entry:
                    self._transform_to_index_entry(
                        resource,
                        _src_entry[field_name],
                        field_content,
                        field_conf["fields"].items(),
                    )
                    self.index_uow.repo.assign_field(
                        _index_entry, field_name, field_content
                    )

            elif field_conf["type"] in (
                "integer",
                "string",
                "number",
                "boolean",
                "long_string",
            ):
                if field_name in _src_entry:
                    field_content = _src_entry[field_name]
                    self.index_uow.repo.assign_field(
                        _index_entry, field_name, field_content
                    )
