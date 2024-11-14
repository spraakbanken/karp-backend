import logging
import typing

from karp.lex.domain.dtos import EntryDto
from karp.search.infrastructure.es import mapping_repo

logger = logging.getLogger(__name__)


def transform(resource_config, src_entry: EntryDto) -> tuple[str, dict]:
    entry = {}
    for mapped_name, field in mapping_repo.internal_fields.items():
        entry[field.name] = getattr(src_entry, mapped_name)
    _transform_to_index_entry(
        src_entry.entry,
        entry,
        resource_config.fields.items(),
    )
    return str(src_entry.id), entry


def _transform_to_index_entry(
    _src_entry: typing.Dict,
    _index_entry: typing.Dict,
    fields,
):
    for field_name, field_conf in fields:
        field_content = None

        if field_conf.collection:
            field_content = []
            if field_name in _src_entry:
                for subfield in _src_entry[field_name]:
                    if field_conf.type == "object":
                        subfield_content = {}
                        _transform_to_index_entry(
                            subfield,
                            subfield_content,
                            field_conf.fields.items(),
                        )
                        field_content.append(subfield_content)
                    else:
                        field_content.append(subfield)
                _index_entry[field_name] = field_content

        elif field_conf.type == "object":
            field_content = {}
            if field_name in _src_entry:
                _transform_to_index_entry(
                    _src_entry[field_name],
                    field_content,
                    field_conf.fields.items(),
                )
                _index_entry[field_name] = field_content

        elif field_conf.type in (
            "integer",
            "string",
            "number",
            "boolean",
            "long_string",
        ):
            if field_name in _src_entry:
                field_content = _src_entry[field_name]
                _index_entry[field_name] = field_content
