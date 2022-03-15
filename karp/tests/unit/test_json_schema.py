from karp.lex.domain.value_objects.entry_schema import EntrySchema
import pytest

from karp.utility.json_schema import create_entry_json_schema

CONFIG_PLACES = """{
  "resource_id": "places",
  "resource_name": "Platser i Sverige",
  "fields": {
    "name": {
      "type": "string",
      "required": true
    },
    "municipality": {
      "collection": true,
      "type": "number",
      "required": true
    },
    "population": {
      "type": "number"
    },
    "area": {
      "type": "number"
    },
    "density": {
      "type": "number"
    },
    "code": {
      "type": "number",
      "required": true
    }
  },
  "sort": "name",
  "id": "code"
}"""


def test_create_json_schema(json_schema_config):
    json_schema = create_entry_json_schema(json_schema_config["fields"])
    assert json_schema["type"] == "object"


class TestCreateJsonSchema:
    @pytest.mark.parametrize(
        'field_type', ['long_string']
    )
    def test_create_with_type(self, field_type: str):
        resource_config = {'field_name': {'type': field_type}}
        json_schema = create_entry_json_schema(resource_config)
        _entry_schema = EntrySchema(json_schema)
