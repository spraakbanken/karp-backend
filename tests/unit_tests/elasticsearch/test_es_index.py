from unittest import mock

from karp.elasticsearch.index import _create_es_mapping, EsIndex
from karp.elasticsearch.es_observer import OnPublish


def test_create_es_mapping_empty():
    config = {"fields": {}}
    mapping = _create_es_mapping(config)

    assert mapping == {"dynamic": False, "properties": {}}


def test_create_es_mapping_string():
    config = {"fields": {"test": {"type": "string"}}}
    mapping = _create_es_mapping(config)

    assert mapping == {
        "dynamic": False,
        "properties": {
            "test": {"fields": {"raw": {"type": "keyword"}}, "type": "text"}
        },
    }


def test_create_es_mapping_string_skip_raw():
    config = {"fields": {"test": {"type": "string", "skip_raw": True}}}
    mapping = _create_es_mapping(config)

    assert mapping == {
        "dynamic": False,
        "properties": {"test": {"type": "text"}},
    }


def test_es_index_register_unregister_on_publish():
    es_index = EsIndex(None)

    on_publish = OnPublish()

    es_index.register_publish_observer(on_publish)

    assert on_publish in es_index.publish_notifier.observers

    es_index.unregister_publish_observer(on_publish)

    assert on_publish not in es_index.publish_notifier.observers


def test_es_index_publish_notifies_observer():
    es_mock = mock.Mock()
    on_publish_mock = mock.Mock(spec=OnPublish)

    es_index = EsIndex(es_mock)

    es_index.register_publish_observer(on_publish_mock)

    alias_name = "alias"
    index_name = "index"

    es_index.publish_index(alias_name, index_name)

    assert on_publish_mock.mock_calls == [
        mock.call.update(alias_name=alias_name, index_name=index_name)
    ]
