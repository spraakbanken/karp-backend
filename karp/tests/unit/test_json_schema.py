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


@pytest.fixture()
def problem_config() -> dict:
    return {
        "resource_id": "konstruktikon",
        "resource_name": "Konstruktikon",
        "fields": {
            "cat": {"type": "string"},
            "illustration": {"type": "string"},
            "cee": {"type": "string", "collection": True},
            "coll": {"type": "string", "collection": True},
            "createdBy": {"type": "string"},
            "definition": {"type": "string"},
            "examples": {"type": "string", "collection": True},
            "entryStatus": {"type": "string"},
            "intConstElem": {
                "type": "object",
                "fields": {
                    "role": {"type": "string"},
                    "name": {"type": "string"},
                    "cat": {"type": "string"},
                    "lu": {"type": "string"},
                    "gfunc": {"type": "string"},
                    "msd": {"type": "string"},
                    "aux": {"type": "string"},
                },
                "collection": True,
            },
            "extConstElem": {
                "type": "object",
                "fields": {
                    "role": {"type": "string"},
                    "name": {"type": "string"},
                    "cat": {"type": "string"},
                    "lu": {"type": "string"},
                    "gfunc": {"type": "string"},
                    "msd": {"type": "string"},
                    "aux": {"type": "string"},
                },
                "collection": True,
            },
            "inheritance": {"type": "string", "collection": True},
            "type": {"type": "string", "collection": True},
            "structure": {"type": "string", "collection": True},
            "constructionID": {"type": "string", "required": True},
            "BCxnID": {"type": "string"},
            "evokes": {"type": "string", "collection": True},
            "comment": {"type": "string"},
            "reference": {"type": "string"},
            "internal_comment": {"type": "string"},
        },
        "sort": "constructionID",
        "protected": {"read": False},
        "id": "constructionID",
    }


def test_error(problem_config: dict):
    json_schema = create_entry_json_schema(problem_config["fields"])
    _entry_schema = EntrySchema(json_schema)


def test_create_json_schema(json_schema_config):
    json_schema = create_entry_json_schema(json_schema_config["fields"])
    assert json_schema["type"] == "object"


class TestCreateJsonSchema:
    @pytest.mark.parametrize("field_type", ["long_string"])
    def test_create_with_type(self, field_type: str):
        resource_config = {"field_name": {"type": field_type}}
        json_schema = create_entry_json_schema(resource_config)
        _entry_schema = EntrySchema(json_schema)
