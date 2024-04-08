import logging
import typing

from karp.lex.domain.dtos import EntryDto
from karp.search.domain.index_entry import IndexEntry

logger = logging.getLogger(__name__)


def transform(resource_config, src_entry: EntryDto) -> IndexEntry:
    entry = create_empty_object()
    assign_field(entry, "_entry_version", src_entry.version)
    assign_field(entry, "_last_modified", src_entry.last_modified)
    assign_field(entry, "_last_modified_by", src_entry.last_modified_by)
    _transform_to_index_entry(
        src_entry.entry,
        entry,
        resource_config["fields"].items(),
    )
    return IndexEntry(id=str(src_entry.id), entry=entry)


def _transform_to_index_entry(
    _src_entry: typing.Dict,
    _index_entry: typing.Dict,
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
                        add_to_list_field(field_content, subfield_content)
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


def create_empty_object() -> typing.Dict:
    return {}


def assign_field(_index_entry: typing.Dict, field_name: str, part):
    _index_entry[field_name] = part


def add_to_list_field(elems: typing.List, elem):
    elems.append(elem)
