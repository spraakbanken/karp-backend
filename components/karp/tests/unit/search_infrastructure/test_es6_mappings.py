from typing import Dict, Optional

import pytest

from karp.search_infrastructure.repositories.es6_indicies import create_es6_mapping


class TestCreateEs6Mapping:
    def test_minimal_valid_input(self):
        data = {"fields": {}}
        mapping = create_es6_mapping(data)

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
                {"type": "text", "fields": {"raw": {"type": "keyword"}}},
            ),
            ("name", {"type": "long_string"}, {"type": "text"}),
        ],
    )
    def test_standard_types(
        self, field: str, field_def: Dict, expected_property: Optional[Dict]
    ):
        data = {
            "fields": {
                field: field_def,
            },
        }
        mapping = create_es6_mapping(data)
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
                    "properties": {
                        "first": {
                            "type": "text",
                            "fields": {"raw": {"type": "keyword"}},
                        }
                    }
                },
            ),
            ("name", {"type": "number"}, {"type": "double"}),
            ("name", {"type": "integer"}, {"type": "long"}),
            (
                "name",
                {"type": "string"},
                {"type": "text", "fields": {"raw": {"type": "keyword"}}},
            ),
            ("name", {"type": "long_string"}, {"type": "text"}),
        ],
    )
    def test_complex_types(
        self, field: str, field_def: Dict, expected_property: Optional[Dict]
    ):
        data = {
            "fields": {
                field: field_def,
            },
        }
        mapping = create_es6_mapping(data)
        assert field in mapping["properties"]
        expected_property = expected_property or field_def
        assert mapping["properties"][field] == expected_property

    def test_sort(self):
        data = {"fields": {"name": {"type": "string"}}, "sort": ["name"]}

        mapping = create_es6_mapping(data)

        expected = {
            "dynamic": False,
            "properties": {
                "name": {"type": "text", "fields": {"raw": {"type": "keyword"}}}
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
                            "unicodeSetFilter": "[^åäöÅÄÖ]",
                        },
                        "swedish_sort": {"language": "sv", "type": "icu_collation"},
                    },
                }
            },
        }

        assert mapping == expected

    @pytest.mark.skip()
    def test_sort_large(self):
        data = {"fields": {"name": {"type": "string"}}, "sort": ["name"]}

        mapping = create_es6_mapping(data)

        expected = {
            "properties": {
                "name": {"type": "text", "fields": {"raw": {"type": "keyword"}}}
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
                        "clean_lastname": {
                            "pattern": "^(af|von) ",
                            "replacement": "",
                            "type": "pattern_replace",
                        },
                        "compound": {
                            "pattern": "-",
                            "replacement": "",
                            "type": "pattern_replace",
                        },
                        "init": {
                            "pattern": "^(.).*",
                            "replacement": "$1",
                            "type": "pattern_replace",
                        },
                        "links": {
                            "pattern": "\\[([^\\]]*)\\](\\([^\\)]*\\))?",
                            "replacement": "$1",
                            "type": "pattern_replace",
                        },
                        "pics": {
                            "pattern": "!\\[[^\\]]*\\](\\([^\\)]*\\))?",
                            "replacement": "",
                            "type": "pattern_replace",
                        },
                        "remove_slash_filter": {
                            "pattern": "(.*)/(.+)/(.*)",
                            "replacement": "$1$2$3",
                            "type": "pattern_replace",
                        },
                        "removespecials": {
                            "pattern": "[^A-Za-zÀÁÂÄÅÆÇÈÉÊËÌÍÎÏÑÒÓÔÖØÙÚÛÜàáâäåæçèéêëìíîïñòóôøöùúûü]",
                            "replacement": "",
                            "type": "pattern_replace",
                        },
                        "slash_filter": {
                            "pattern": "(.*)/(.+)/(.*)",
                            "replacement": "$2",
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
                        "underscore": {
                            "pattern": "_*((~_)*)_*",
                            "replacement": "$1",
                            "type": "pattern_replace",
                        },
                    },
                    "filter": {
                        "swedish_folding": {
                            "type": "icu_folding",
                            "unicodeSetFilter": "[^åäöÅÄÖ]",
                        },
                        "swedish_sort": {"language": "sv", "type": "icu_collation"},
                    },
                }
            },
        }

        assert mapping == expected
