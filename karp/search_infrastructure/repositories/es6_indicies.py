from datetime import datetime
import logging
import re
from typing import Dict, Iterable, List, Optional, Any, Tuple, Union

import elasticsearch
from elasticsearch import exceptions as es_exceptions

from karp.foundation.events import EventBus

from karp.lex.domain.entities import Entry
from karp.search.application.repositories import (
    Index,
    IndexEntry,
    IndexUnitOfWork,
)
from karp.search.domain.errors import UnsupportedField
from karp.search_infrastructure.elasticsearch6 import Es6MappingRepository


logger = logging.getLogger(__name__)


class Es6Index(Index):
    def __init__(
        self,
        es: elasticsearch.Elasticsearch,
        mapping_repo: Es6MappingRepository,
    ):
        self.es = es
        self.mapping_repo = mapping_repo

    @property
    def seen(self):
        return []

    def create_index(self, resource_id: str, config):
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

        index_name = self.mapping_repo.get_index_name(resource_id)
        logger.info("creating index", extra={"index_name": index_name, "body": body})
        result = self.es.indices.create(index=index_name, body=body)
        if "error" in result:
            logger.error(
                "failed to create index", extra={"index_name": index_name, "body": body}
            )
            raise RuntimeError("failed to create index")
        logger.info("index created")
        return index_name

    def publish_index(self, resource_id: str):
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

    def add_entries(self, resource_id: str, entries: Iterable[IndexEntry]):
        index_name = self.mapping_repo.get_index_name(resource_id)
        index_to_es = []
        for entry in entries:
            assert isinstance(entry, IndexEntry)
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

    def delete_entry(
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
        logger.info(
            "deleting entry", extra={"entry_id": entry_id, "resource_id": resource_id}
        )
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


def _create_es_mapping(config):
    es_mapping = {"dynamic": False, "properties": {}}

    fields = config["fields"]

    def recursive_field(parent_schema, parent_field_name, parent_field_def):
        if parent_field_def.get("virtual", False):
            fun = parent_field_def["function"]
            if list(fun.keys())[0] == "multi_ref":
                res_object = fun["multi_ref"]["result"]
                recursive_field(parent_schema, f"v_{parent_field_name}", res_object)
            if "result" in fun:
                res_object = fun["result"]
                recursive_field(parent_schema, f"v_{parent_field_name}", res_object)
            return
        if parent_field_def.get("ref"):
            if "field" in parent_field_def["ref"]:
                res_object = parent_field_def["ref"]["field"]
            else:
                res_object = {}
                res_object.update(parent_field_def)
                del res_object["ref"]
            recursive_field(parent_schema, f"v_{parent_field_name}", res_object)
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


def create_es6_mapping(config: Dict) -> Dict:
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


class Es6IndexUnitOfWork(IndexUnitOfWork):
    def __init__(
        self,
        es: elasticsearch.Elasticsearch,
        event_bus: EventBus,
        mapping_repo: Es6MappingRepository,
    ) -> None:
        super().__init__(event_bus=event_bus)
        self._index = Es6Index(
            es=es,
            mapping_repo=mapping_repo,
        )

    # @classmethod
    # def from_dict(cls, **kwargs):
    #     return cls()

    def _commit(self):
        logger.debug("Calling _commit in Es6IndexUnitOfWork")

    def rollback(self):
        return super().rollback()

    @property
    def repo(self) -> Es6Index:
        return self._index

    def _close(self):
        pass
