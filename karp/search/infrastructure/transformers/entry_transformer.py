import logging
import typing

from karp.lex.domain import errors as lex_errors
from karp.lex.domain.dtos import EntryDto
from karp.search.domain import IndexEntry

logger = logging.getLogger(__name__)


def transform(resource, src_entry: EntryDto) -> IndexEntry:
    index_entry = create_empty_object()
    index_entry.id = str(src_entry.id)
    assign_field(index_entry, "_entry_version", src_entry.version)
    assign_field(index_entry, "_last_modified", src_entry.last_modified)
    assign_field(index_entry, "_last_modified_by", src_entry.last_modified_by)
    if not resource:
        raise lex_errors.ResourceNotFound(None, resource_id=resource.resource_id)
    _transform_to_index_entry(
        src_entry.entry,
        index_entry,
        resource.config["fields"].items(),
    )
    return index_entry


def _transform_to_index_entry(
    _src_entry: typing.Dict,
    _index_entry: IndexEntry,
    fields,
):
    for field_name, field_conf in fields:
        field_content = None

        if field_conf.get("collection"):
            field_content = []
            if field_name in _src_entry:
                for subfield in _src_entry[field_name]:
                    if field_conf["type"] == "object":
                        subfield_content = create_empty_object()
                        _transform_to_index_entry(
                            subfield,
                            subfield_content,
                            field_conf["fields"].items(),
                        )
                        add_to_list_field(field_content, subfield_content.entry)
                    else:
                        add_to_list_field(field_content, subfield)
                assign_field(_index_entry, field_name, field_content)

        elif field_conf["type"] == "object":
            field_content = create_empty_object()
            if field_name in _src_entry:
                _transform_to_index_entry(
                    _src_entry[field_name],
                    field_content,
                    field_conf["fields"].items(),
                )
                assign_field(_index_entry, field_name, field_content)

        elif field_conf["type"] in (
            "integer",
            "string",
            "number",
            "boolean",
            "long_string",
        ):
            if field_name in _src_entry:
                field_content = _src_entry[field_name]
                assign_field(_index_entry, field_name, field_content)


def create_empty_object() -> IndexEntry:
    return IndexEntry(id="", entry={})


def assign_field(_index_entry: IndexEntry, field_name: str, part):
    if isinstance(part, IndexEntry):
        part = part.entry
    _index_entry.entry[field_name] = part


def add_to_list_field(elems: typing.List, elem):
    if isinstance(elem, IndexEntry):
        elem = elem.entry
    elems.append(elem)
