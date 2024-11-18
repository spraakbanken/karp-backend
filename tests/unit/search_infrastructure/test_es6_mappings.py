from typing import Dict, Optional

import pytest

from karp.lex.domain.value_objects import Field, ResourceConfig
from karp.search.infrastructure.es.indices import _create_es_mapping


class TestCreateEsMapping:
    def test_minimal_valid_input(self):
        data = ResourceConfig(resource_id="", config_str="", fields={})
        mapping = _create_es_mapping(data)

        assert mapping["properties"] == {}

    @pytest.mark.parametrize(
        "field, field_def, expected_property",
        [
            ("name", Field(type="boolean"), {"type": "boolean"}),
            ("name", Field(type="number"), {"type": "double"}),
            ("name", Field(type="integer"), {"type": "long"}),
            (
                "name",
                Field(type="string"),
                {
                    "type": "text",
                    "fields": {
                        "raw": {"type": "keyword"},
                        "sort": {
                            "index": False,
                            "type": "icu_collation_keyword",
                            "language": "sv",
                        },
                    },
                },
            ),
        ],
    )
    def test_standard_types(self, field: str, field_def: Field, expected_property: Optional[Dict]):
        data = ResourceConfig(resource_id="", config_str="", fields={field: field_def})
        mapping = _create_es_mapping(data)
        assert field in mapping["properties"]
        assert mapping["properties"][field] == expected_property

    @pytest.mark.parametrize(
        "field, field_def, expected_property",
        [
            (
                "name",
                Field(type="object", fields={"first": {"type": "string"}}),
                {
                    "properties": {
                        "first": {
                            "type": "text",
                            "fields": {
                                "raw": {"type": "keyword"},
                                "sort": {
                                    "index": False,
                                    "type": "icu_collation_keyword",
                                    "language": "sv",
                                },
                            },
                        },
                    },
                },
            ),
            (
                "name",
                Field(type="object", collection=True, fields={"first": {"type": "string"}}),
                {
                    "type": "nested",
                    "properties": {
                        "first": {
                            "type": "text",
                            "fields": {
                                "raw": {"type": "keyword"},
                                "sort": {
                                    "index": False,
                                    "type": "icu_collation_keyword",
                                    "language": "sv",
                                },
                            },
                        },
                    },
                },
            ),
            ("name", Field(type="number"), {"type": "double"}),
            ("name", Field(type="integer"), {"type": "long"}),
            (
                "name",
                Field(type="string"),
                {
                    "type": "text",
                    "fields": {
                        "raw": {"type": "keyword"},
                        "sort": {
                            "index": False,
                            "type": "icu_collation_keyword",
                            "language": "sv",
                        },
                    },
                },
            ),
        ],
    )
    def test_complex_types(self, field: str, field_def: Field, expected_property: Optional[Dict]):
        data = ResourceConfig(resource_id="", config_str="", fields={field: field_def})
        mapping = _create_es_mapping(data)
        assert field in mapping["properties"]
        expected_property = expected_property or field_def.model_dump()
        assert mapping["properties"][field] == expected_property

    def test_sort(self):
        data = ResourceConfig(resource_id="", config_str="", fields={"name": Field(type="string")}, sort=["name"])

        mapping = _create_es_mapping(data)

        expected = {
            "dynamic": False,
            "properties": {
                "name": {
                    "type": "text",
                    "fields": {
                        "raw": {"type": "keyword"},
                        "sort": {
                            "index": False,
                            "type": "icu_collation_keyword",
                            "language": "sv",
                        },
                    },
                }
            },
        }

        assert mapping == expected
