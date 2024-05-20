from typing import Dict, Optional  # noqa: I001

import pytest

from karp.search.infrastructure.es.indices import create_es_mapping


class TestCreateEsMapping:
    def test_minimal_valid_input(self):  # noqa: ANN201
        data = {"fields": {}}
        mapping = create_es_mapping(data)

        assert mapping["properties"] == {}

    @pytest.mark.parametrize(
        "field, field_def, expected_property",
        [
            ("name", {"type": "boolean"}, {}),
            ("name", {"type": "number"}, {"type": "double"}),
            ("name", {"type": "integer"}, {"type": "long"}),
            (
                "name",
                {"type": "string"},
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
    def test_standard_types(  # noqa: ANN201
        self, field: str, field_def: Dict, expected_property: Optional[Dict]
    ):
        data = {
            "fields": {
                field: field_def,
            },
        }
        mapping = create_es_mapping(data)
        assert field in mapping["properties"]
        expected_property = expected_property or field_def
        assert mapping["properties"][field] == expected_property

    @pytest.mark.parametrize(
        "field, field_def, expected_property",
        [
            (
                "name",
                {"type": "object", "fields": {"first": {"type": "string"}}},
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
            ("name", {"type": "number"}, {"type": "double"}),
            ("name", {"type": "integer"}, {"type": "long"}),
            (
                "name",
                {"type": "string"},
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
    def test_complex_types(  # noqa: ANN201
        self, field: str, field_def: Dict, expected_property: Optional[Dict]
    ):
        data = {
            "fields": {
                field: field_def,
            },
        }
        mapping = create_es_mapping(data)
        assert field in mapping["properties"]
        expected_property = expected_property or field_def
        assert mapping["properties"][field] == expected_property

    def test_sort(self):  # noqa: ANN201
        data = {"fields": {"name": {"type": "string"}}, "sort": ["name"]}

        mapping = create_es_mapping(data)

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
            "settings": {
                "analysis": {
                    "analyzer": {
                        "default": {
                            "char_filter": [
                                "compound",
                                "swedish_aa",
                                "swedish_ae",
                                "swedish_oe",
                            ],
                            "filter": ["swedish_folding", "lowercase"],
                            "tokenizer": "standard",
                        },
                    },
                    "char_filter": {
                        "compound": {
                            "pattern": "-",
                            "replacement": "",
                            "type": "pattern_replace",
                        },
                        "swedish_aa": {
                            "pattern": "[Ǻǻ]",
                            "replacement": "å",
                            "type": "pattern_replace",
                        },
                        "swedish_ae": {
                            "pattern": "[æÆǞǟ]",
                            "replacement": "ä",
                            "type": "pattern_replace",
                        },
                        "swedish_oe": {
                            "pattern": "[ØøŒœØ̈ø̈ȪȫŐőÕõṌṍṎṏȬȭǾǿǬǭŌōṒṓṐṑ]",
                            "replacement": "ö",
                            "type": "pattern_replace",
                        },
                    },
                    "filter": {
                        "swedish_folding": {
                            "type": "icu_folding",
                            "unicode_set_filter": "[^åäöÅÄÖ]",
                        },
                    },
                }
            },
        }

        assert mapping == expected
