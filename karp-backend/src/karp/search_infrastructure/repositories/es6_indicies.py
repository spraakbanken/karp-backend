import logging  # noqa: D100
import re  # noqa: F401
import typing
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union  # noqa: F401

import elasticsearch
from elasticsearch import exceptions as es_exceptions  # noqa: F401
from karp.lex.domain.entities import Entry
from karp.search.application.repositories import (
    IndexEntry,
)
from karp.search_infrastructure.elasticsearch6 import Es6MappingRepository

logger = logging.getLogger(__name__)


class Es6Index:
    def __init__(
        self,
        es: elasticsearch.Elasticsearch,
        mapping_repo: Es6MappingRepository,
    ):
        self.es = es
        self.mapping_repo = mapping_repo

    def create_index(self, resource_id: str, config):  # noqa: ANN201, D102
        logger.info("creating es mapping")
        mapping = create_es6_mapping(config)

        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 1,
            "refresh_interval": -1,
        }
        if "settings" in mapping:
            settings |= mapping["settings"]
            del mapping["settings"]
        properties = mapping["properties"]
        properties["freetext"] = {"type": "text"}
        disabled_property = {"enabled": False}
        properties["_entry_version"] = disabled_property
        properties["_last_modified"] = disabled_property
        properties["_last_modified_by"] = disabled_property

        body = {
            "settings": settings,
            "mappings": {"entry": mapping},
        }

        index_alias_name = self.mapping_repo.create_index_and_alias_name(resource_id)
        logger.info("creating index", extra={"index_alias_name": index_alias_name, "body": body})
        result = self.es.indices.create(index=index_alias_name["index_name"], body=body)
        if "error" in result:
            logger.error(
                "failed to create index",
                extra={"index_name": index_alias_name["index_name"], "body": body},
            )
            raise RuntimeError("failed to create index")
        logger.info("index created")
        return index_alias_name

    def delete_index(self, resource_id: str):
        index_name = self.mapping_repo.get_index_name(resource_id)
        alias_name = self.mapping_repo.get_alias_name(resource_id)
        self.es.indices.delete(index=index_name)
        self.mapping_repo.delete_from_config(resource_id)

    def publish_index(self, resource_id: str):  # noqa: ANN201, D102
        alias_name = self.mapping_repo.get_alias_name(resource_id)
        if self.es.indices.exists_alias(name=alias_name):
            self.es.indices.delete_alias(name=alias_name, index="*")

        index_name = self.mapping_repo.get_index_name(resource_id)
        self.mapping_repo.on_publish_resource(alias_name, index_name)
        logger.info(
            "publishing resource",
            extra={
                "resource_id": resource_id,
                "index_name": index_name,
                "alias_name": alias_name,
            },
        )
        self.es.indices.put_alias(name=alias_name, index=index_name)

    def add_entries(  # noqa: D102, ANN201
        self, resource_id: str, entries: Iterable[IndexEntry]
    ):
        index_name = self.mapping_repo.get_index_name(resource_id)
        index_to_es = []
        for entry in entries:
            assert isinstance(entry, IndexEntry)  # noqa: S101
            # entry.update(metadata.to_dict())
            index_to_es.append(
                {
                    "_index": index_name,
                    "_id": entry.id,
                    "_type": "entry",
                    "_source": entry.entry,
                }
            )

        elasticsearch.helpers.bulk(self.es, index_to_es, refresh=True)

    def delete_entry(  # noqa: ANN201, D102
        self,
        resource_id: str,
        *,
        entry_id: Optional[str] = None,
        entry: Optional[Entry] = None,
    ):
        if not entry and not entry_id:
            raise ValueError("Must give either 'entry' or 'entry_id'.")
        if entry:
            entry_id = entry.entry_id
        logger.info("deleting entry", extra={"entry_id": entry_id, "resource_id": resource_id})
        index_name = self.mapping_repo.get_index_name(resource_id)
        try:
            self.es.delete(
                index=index_name,
                doc_type="entry",
                id=entry_id,
                refresh=True,
            )
        except elasticsearch.exceptions.ElasticsearchException:
            logger.exception(
                "Error deleting entry",
                extra={
                    "entry_id": entry_id,
                    "resource_id": resource_id,
                    "index_name": index_name,
                },
            )

    def create_empty_object(self) -> IndexEntry:  # noqa: D102
        return IndexEntry(id="", entry={})

    def assign_field(  # noqa: ANN201, D102
        self, _index_entry: IndexEntry, field_name: str, part
    ):
        if isinstance(part, IndexEntry):
            part = part.entry
        _index_entry.entry[field_name] = part

    def add_to_list_field(self, elems: typing.List, elem):  # noqa: ANN201, D102
        if isinstance(elem, IndexEntry):
            elem = elem.entry
        elems.append(elem)


def _create_es_mapping(config):  # noqa: C901, ANN202
    es_mapping = {"dynamic": False, "properties": {}}

    fields = config["fields"]

    def recursive_field(  # noqa: ANN202, C901
        parent_schema, parent_field_name, parent_field_def
    ):
        if parent_field_def["type"] != "object":
            # TODO this will not work when we have user defined types, s.a. saldoid
            # TODO number can be float/non-float, strings can be keyword or text in need of analyzing etc.
            if parent_field_def["type"] == "integer":
                mapped_type = "long"
            elif parent_field_def["type"] == "number":
                mapped_type = "double"
            elif parent_field_def["type"] == "boolean":
                mapped_type = "boolean"
            elif parent_field_def["type"] == "string":
                mapped_type = "text"
            elif parent_field_def["type"] == "long_string":
                mapped_type = "text"
            else:
                mapped_type = "keyword"
            result = {"type": mapped_type}
            if parent_field_def["type"] == "string":
                result["fields"] = {"raw": {"type": "keyword"}}
        else:
            result = {"properties": {}}

            for child_field_name, child_field_def in parent_field_def["fields"].items():
                recursive_field(result, child_field_name, child_field_def)

        parent_schema["properties"][parent_field_name] = result

    for field_name, field_def in fields.items():
        print(f"creating mapping for field '{field_name}'")
        recursive_field(es_mapping, field_name, field_def)

    return es_mapping


def create_es6_mapping(config: Dict) -> Dict:  # noqa: D103
    mapping = _create_es_mapping(config)
    mapping["settings"] = {
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
                }
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
    }
    return mapping
