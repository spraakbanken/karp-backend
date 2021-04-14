from typing import Dict
import pytest

from karp.indexmgr import transform_to_index_entry
from karp import resourcemgr


@pytest.mark.parametrize(
    "resource_id,fields_config,src_entry,expected",
    [
        ("alphalex", {}, {}, {}),
        ("alphalex", {"a": {"type": "integer"}}, {"a": 1}, {"a": 1}),
        (
            "alphalex",
            {"a": {"type": "integer", "collection": True}},
            {"a": [1]},
            {"a": [1]},
        ),
        ("alphalex", {"a": {"type": "number"}}, {"a": 1.2}, {"a": 1.2}),
        (
            "alphalex",
            {"a": {"type": "number", "collection": True}},
            {"a": [1.2]},
            {"a": [1.2]},
        ),
        ("alphalex", {"a": {"type": "string"}}, {"a": "s"}, {"a": "s"}),
        (
            "alphalex",
            {"a": {"type": "string", "skip_raw": True}},
            {"a": "s"},
            {"a": "s"},
        ),
        (
            "alphalex",
            {"a": {"type": "string", "collection": True}},
            {"a": ["s"]},
            {"a": ["s"]},
        ),
        (
            "alphalex",
            {"a": {"type": "object", "fields": {"b": {"type": "integer"}}}},
            {"a": {"b": 1}},
            {"a": {"b": 1}},
        ),
        (
            "alphalex",
            {
                "a": {
                    "type": "object",
                    "collection": True,
                    "fields": {"b": {"type": "integer"}},
                }
            },
            {"a": [{"b": 1}]},
            {"a": [{"b": 1}]},
        ),  # 9
        (
            "alphalex",
            {"a": {"type": "object", "fields": {"b": {"type": "string"}}}},
            {"a": {"b": "s"}},
            {"a": {"b": "s"}},
        ),  # 10
        (
            "alphalex",
            {
                "a": {
                    "type": "object",
                    "collection": True,
                    "fields": {"b": {"type": "string"}},
                }
            },
            {"a": [{"b": "s"}]},
            {"a": [{"b": "s"}]},
        ),  # 11
        (
            "alphalex",
            {
                "etymology": {
                    "type": "object",
                    "fields": {
                        "language": {"type": "string"},
                        "form": {"type": "string"},
                        "description": {"type": "string"},
                    },
                    "collection": True,
                },
                "lemgram": {"type": "string", "required": True},
            },
            {
                "lemgram": "väffse..e.1",
                "etymology": [
                    {"language": "dan", "form": "hveps"},
                    {"language": "deu", "form": "wespe"},
                ],
            },
            {
                "lemgram": "väffse..e.1",
                "etymology": [
                    {"language": "dan", "form": "hveps"},
                    {"language": "deu", "form": "wespe"},
                ],
            },
        ),  # 12
        (
            "municipalities",
            {
                "places": {
                    "virtual": True,
                    "type": "object",
                    "collection": True,
                    "function": {
                        "multi_ref": {
                            "resource_id": "places",
                            "resource_version": 1,
                            "field": "municipality",
                            "result": {
                                "type": "object",
                                "fields": {
                                    "code": {"type": "integer"},
                                    "name": {"type": "string"},
                                },
                            },
                            "test": {"contains": [{"self": "code"}]},
                        }
                    },
                },
                "code": {"type": "integer"},
            },
            {"code": 1},
            {
                "code": 1,
                "v_places": [
                    {"code": 1, "name": "Grund test"},
                    {"code": 2, "name": "Grunds"},
                ],
            },
        ),
        (
            "places",
            {
                "larger_place": {
                    "type": "integer",
                    "ref": {
                        "field": {
                            "type": "object",
                            "fields": {
                                "code": {"type": "integer"},
                                "name": {"type": "string"},
                            },
                        }
                    },
                },
            },
            {"larger_place": 1},
            {"larger_place": 1, "v_larger_place": {"code": 1, "name": "Grund test"}},
        ),
        (
            "places",
            {
                "neighbours": {
                    "type": "integer",
                    "collection": True,
                    "ref": {
                        "field": {
                            "type": "object",
                            "collection": True,
                            "fields": {
                                "code": {"type": "integer"},
                                "name": {"type": "string"},
                            },
                        }
                    },
                },
            },
            {"neighbours": [1, 2]},
            {
                "neighbours": [1, 2],
                "v_neighbours": [
                    {"code": 1, "name": "Grund test"},
                    {"code": 2, "name": "Grunds"},
                ],
            },
        ),
        (
            "places",
            {
                "test_field": {
                    "type": "integer",
                    "ref": {
                        "resource_id": "municipalities",
                        "resource_version": 1,
                        "field": {
                            "type": "object",
                            "fields": {
                                "code": {"type": "integer"},
                                "name": {"type": "string"},
                                "state": {"type": "string"},
                            },
                        },
                    },
                    "required": True,
                },
            },
            {
                "test_field": 1,
            },
            {
                "test_field": 1,
                "v_test_field": {
                    "code": 1,
                    "name": "Luleå kommun",
                    "state": "Norrbottens län",
                },
            },
        ),
        (
            "places",
            {
                "municipality": {
                    "collection": True,
                    "type": "integer",
                    "ref": {
                        "resource_id": "municipalities",
                        "resource_version": 1,
                        "field": {
                            "collection": True,
                            "type": "object",
                            "fields": {
                                "code": {"type": "integer"},
                                "name": {"type": "string"},
                                "state": {"type": "string"},
                            },
                        },
                    },
                    "required": True,
                },
            },
            {
                "municipality": [1, 2],
            },
            {
                "municipality": [1, 2],
                "v_municipality": [
                    {"code": 1, "name": "Luleå kommun", "state": "Norrbottens län"},
                    {"code": 2, "name": "Norsjö kommun", "state": "Västerbottens län"},
                ],
            },
        ),
    ],
)
def test_transform_to_index_entry(
    es,
    client_with_entries_scope_session,
    resource_id: str,
    fields_config: Dict,
    src_entry: Dict,
    expected: Dict,
):
    # app = app_with_data_f_scope_session(use_elasticsearch=True)
    with client_with_entries_scope_session.application.app_context():
        resource = resourcemgr.get_resource(resource_id)
        index_entry = transform_to_index_entry(
            resource, src_entry, fields_config.items()
        )

        assert index_entry == expected
