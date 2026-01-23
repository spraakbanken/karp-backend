import logging
from datetime import datetime
from typing import Any, Iterable

import elasticsearch
import elasticsearch.helpers
from elasticsearch.exceptions import NotFoundError
from injector import inject

from karp.lex.domain.value_objects import ResourceConfig
from karp.main.errors import KarpError
from karp.search.domain.index_entry import IndexEntry
from karp.search.infrastructure.es import mapping_repo as es_mapping_repo

from .mapping_repo import EsMappingRepository

logger = logging.getLogger(__name__)

# settings are the same in all indices
settings = {
    "number_of_shards": 1,
    "number_of_replicas": 1,
    # turns off refreshing, needs to be combined with explicitly making refreshes when adding/deleting
    "refresh_interval": -1,
    "mapping": {"nested_fields": {"limit": 100}},
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
                "unicode_set_filter": "[^åäöÅÄÖ]",
            },
        },
    },
}


class EsIndex:
    @inject
    def __init__(
        self,
        es: elasticsearch.Elasticsearch,
        mapping_repo: EsMappingRepository,
    ):
        self.es = es
        self.mapping_repo = mapping_repo

    def create_index(self, resource_id: str, config: ResourceConfig, create_alias=True):
        logger.info("creating es mapping")
        mapping = _create_es_mapping(config)

        properties = mapping["properties"]
        for field in es_mapping_repo.internal_fields.values():
            properties[field.name] = {"type": field.type}

        body = {
            "settings": settings,
            "mappings": mapping,
        }

        date = datetime.now().strftime("%Y-%m-%d-%H%M%S%f")
        index_name = f"{resource_id}_{date}"
        logger.debug("creating index", extra={"index_name": index_name, "body": body})
        result = self.es.indices.create(index=index_name, body=body)

        if create_alias:
            # create an alias so we can interact with the index using resource_id
            self.create_alias(resource_id, index_name)

        if "error" in result:
            logger.error(
                "failed to create index",
                extra={"index_name": index_name, "body": body},
            )
            raise RuntimeError("failed to create index")
        logger.info("index created")
        return index_name

    def create_alias(self, resource_id, index_name):
        if self.es.indices.exists_alias(name=resource_id):
            self.es.indices.delete_alias(name=resource_id, index="*")
        self.es.indices.put_alias(name=resource_id, index=index_name)

    def delete_index(self, resource_id: str):
        try:
            index_name = self.es.indices.get_alias(name=resource_id).popitem()[0]
            self.es.indices.delete(index=index_name)
        except NotFoundError:
            pass

    def add_entries(self, resource_id: str, entries: Iterable[IndexEntry]):
        index_to_es = (
            {
                "_index": resource_id,
                "_id": entry.id,
                "_source": entry.entry,
            }
            for entry in entries
        )

        try:
            elasticsearch.helpers.bulk(self.es, index_to_es, refresh=True)
        except elasticsearch.helpers.BulkIndexError as e:
            message = [
                "Error inserting data into Elasticsearch. The following errors occured (terminated at 400 characters):"
            ]
            for error in e.errors:
                message.append(str(error["index"])[0:400])
                raise KarpError("\n".join(message)) from None

    def delete_entries(self, resource_id: str, *, entry_ids: Iterable[str], raise_on_error=True) -> dict[str, Any]:
        index_to_es = (
            {
                "_op_type": "delete",
                "_index": resource_id,
                "_id": str(entry_id),
            }
            for entry_id in entry_ids
        )
        _, errors = elasticsearch.helpers.bulk(self.es, index_to_es, refresh=True, raise_on_error=raise_on_error)
        return [error["delete"] for error in errors]


def _create_es_mapping(config):
    es_mapping = {"dynamic": False, "properties": {}}

    fields = config.fields

    def recursive_field(parent_schema, parent_field_name, parent_field_def):
        source_exclude_fields = []
        if parent_field_def.type != "object":
            # TODO this will not work when we have user defined types, s.a. saldoid
            # TODO number can be float/non-float, strings can be keyword or text in need of analyzing etc.
            if parent_field_def.type == "integer":
                mapped_type = "long"
            elif parent_field_def.type == "number":
                mapped_type = "double"
            elif parent_field_def.type == "boolean":
                mapped_type = "boolean"
            elif parent_field_def.type == "string":
                mapped_type = "text"
            elif parent_field_def.type == "dense_vector":
              mapped_type = "dense_vector"
            else:
                mapped_type = "keyword"
            result = {"type": mapped_type}
            if parent_field_def.type == "string" and not parent_field_def.skip_raw:
                result["fields"] = {
                    "raw": {"type": "keyword"},
                    "sort": {"type": "icu_collation_keyword", "index": False, "language": "sv"},
                }
        else:
            result = {"properties": {}}
            if parent_field_def.collection:
                result["type"] = "nested"

            for child_field_name, child_field_def in parent_field_def.fields.items():
                child_source_exclude_fields = recursive_field(result, child_field_name, child_field_def)
                for elem in child_source_exclude_fields:
                    source_exclude_fields.append(parent_field_name + "." + elem)

        if not parent_field_def.store:
            source_exclude_fields.append(parent_field_name)

        parent_schema["properties"][parent_field_name] = result

        return source_exclude_fields

    es_mapping["_source"] = {"excludes": []}
    for field_name, field_def in fields.items():
        logger.info(f"creating mapping for field '{field_name}'")
        source_exclude_fields = recursive_field(es_mapping, field_name, field_def)
        es_mapping["_source"]["excludes"].extend(source_exclude_fields)

    return es_mapping
