import pytest

from karp.indexmgr import transform_to_index_entry
from karp import resourcemgr


@pytest.mark.parametrize(
    "fields_config,src_entry,expected",
    [
        ({}, {}, {}),
        ({"a": {"type": "integer"}}, {"a": 1}, {"a": 1}),
        ({"a": {"type": "integer", "collection": True}}, {"a": [1]}, {"a": [1]}),
        ({"a": {"type": "number"}}, {"a": 1.2}, {"a": 1.2}),
        ({"a": {"type": "number", "collection": True}}, {"a": [1.2]}, {"a": [1.2]}),
        ({"a": {"type": "string"}}, {"a": "s"}, {"a": "s"}),
        ({"a": {"type": "string", "skip_raw": True}}, {"a": "s"}, {"a": "s"}),
        ({"a": {"type": "string", "collection": True}}, {"a": ["s"]}, {"a": ["s"]}),
        (
            {"a": {"type": "object", "fields": {"b": {"type": "integer"}}}},
            {"a": {"b": 1}},
            {"a": {"b": 1}},
        ),
        (
            {
                "a": {
                    "type": "object",
                    "collection": True,
                    "fields": {"b": {"type": "integer"}},
                }
            },
            {"a": [{"b": 1}]},
            {"a": [{"b": 1}]},
        ),
        (
            {"a": {"type": "object", "fields": {"b": {"type": "string"}}}},
            {"a": {"b": "s"}},
            {"a": {"b": "s"}},
        ),
        (
            {
                "a": {
                    "type": "object",
                    "collection": True,
                    "fields": {"b": {"type": "string"}},
                }
            },
            {"a": [{"b": "s"}]},
            {"a": [{"b": "s"}]},
        ),
        (
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
        ),
    ],
)
def test_transform_to_index_entry(
    es, app_with_data_f_scope_session, fields_config, src_entry, expected
):
    app = app_with_data_f_scope_session(use_elasticsearch=True)
    with app.app_context():
        resource = resourcemgr.get_resource("alphalex")
        index_entry = transform_to_index_entry(
            resource, src_entry, fields_config.items()
        )

        assert index_entry == expected
