"""Utilities for working with json_schema."""
from typing import Any


def json_schema_type(in_type: str) -> str:  # noqa: D103
    return "string" if in_type == "long_string" else in_type


def create_entry_json_schema(fields: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Create json_schema from fields definition.

    Args:
        fields (Dict[str, Any]): the fields config to process

    Returns:
        Dict[str]: The json_schema to use.

    """  # noqa: D406, D407
    json_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {},
    }

    def recursive_field(
        parent_schema: dict[str, Any],
        parent_field_name: str,
        parent_field_def: dict[str, Any],
    ) -> None:
        if parent_field_def.get("virtual", False):
            return

        if parent_field_def["type"] != "object":
            # TODO this will not work when we have user defined types, s.a. saldoid
            schema_type = json_schema_type(parent_field_def["type"])
            result: dict[str, Any] = {"type": schema_type}
        else:
            result = {"type": "object", "properties": {}}

            for child_field_name, child_field_def in parent_field_def["fields"].items():
                recursive_field(result, child_field_name, child_field_def)

        if parent_field_def.get("required", False):
            if "required" not in parent_schema:
                parent_schema["required"] = []
            parent_schema["required"].append(parent_field_name)

        if parent_field_def.get("collection", False):
            result = {"type": "array", "items": result}

        parent_schema["properties"][parent_field_name] = result

    for field_name, field_def in fields.items():
        recursive_field(json_schema, field_name, field_def)

    return json_schema
