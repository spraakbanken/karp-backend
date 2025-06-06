"""Utilities for working with json_schema."""

import logging
from typing import Any

import fastjsonschema

from karp.lex.domain import errors

from .resource_config import Field, ResourceConfig

logger = logging.getLogger(__name__)


class EntrySchema:
    def __init__(self, json_schema: dict) -> None:
        if not isinstance(json_schema, dict):
            msg = f"Expecting 'dict', got '{type(json_schema)}'"
            raise TypeError(msg)
        try:
            self._compiled_schema = fastjsonschema.compile(json_schema)
            self.schema = json_schema
        except fastjsonschema.JsonSchemaDefinitionException as e:
            raise errors.InvalidEntrySchema() from e

    def validate_entry(self, json_obj: dict[str, Any]) -> dict[str, Any]:
        """Validate a entry against json schema."""
        try:
            self._compiled_schema(json_obj)
        except fastjsonschema.JsonSchemaException as e:
            logger.warning(f'Entry not valid: {(str(json_obj)[:100] + "...")[:100]}, exception: {e!s}')
            raise errors.InvalidEntry(reason=str(e)) from None
        return json_obj

    @classmethod
    def from_resource_config(cls, resource_config: ResourceConfig) -> "EntrySchema":
        """Create EntrySchema from resource config."""

        return cls(json_schema=create_entry_json_schema(resource_config.fields, resource_config.additional_properties))


def create_entry_json_schema(fields: dict[str, Field], additionalProperties: bool) -> dict[str, Any]:
    """Create json_schema from fields definition.

    Args:
        fields (Dict[str, Field]): the fields config to process

    Returns
        Dict[str]: The json_schema to use.

    """
    json_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {},
    }

    def recursive_field(
        parent_schema: dict[str, Any],
        parent_field_name: str,
        parent_field_def: Field,
    ) -> None:
        if parent_field_def.virtual:
            # This forbids virtual fields from being present in the entry
            result: dict[str, Any] = {"not": {}}
            parent_schema["properties"][parent_field_name] = result
            return  # skip the handling of collection fields down below

        if parent_field_def.type != "object":
            # TODO this will not work when we have user defined types, s.a. saldoid
            schema_type = "string" if parent_field_def.type == "long_string" else parent_field_def.type
            result: dict[str, Any] = {"type": schema_type}
        else:
            result = {"type": "object", "properties": {}}

            for child_field_name, child_field_def in parent_field_def.fields.items():
                recursive_field(result, child_field_name, child_field_def)

        if parent_field_def.required:
            if "required" not in parent_schema:
                parent_schema["required"] = []
            parent_schema["required"].append(parent_field_name)

        if parent_field_def.collection:
            result = {"type": "array", "items": result}

        parent_schema["properties"][parent_field_name] = result

    for field_name, field_def in fields.items():
        recursive_field(json_schema, field_name, field_def)
    json_schema["additionalProperties"] = additionalProperties
    return json_schema
