import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable

import opensearchpy
import opensearchpy.helpers
from opensearchpy.exceptions import NotFoundError

from karp.globals import os_client
from karp.lex.domain.value_objects import ResourceConfig
from karp.main.errors import KarpError
from karp.search.domain.index_entry import IndexEntry
from karp.search.infrastructure.opensearch import mapping_repo

logger = logging.getLogger(__name__)

# settings are the same in all indices
settings = {
    "index": {"knn": True},
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


def create_index(resource_id: str, config: ResourceConfig, call_create_alias=True):
    logger.info("creating es mapping")
    mapping = _create_es_mapping(config)

    properties = mapping["properties"]
    for field in mapping_repo.internal_fields.values():
        properties[field.name] = {"type": field.type}

    body = {
        "settings": settings,
        "mappings": mapping,
    }

    date = datetime.now().strftime("%Y-%m-%d-%H%M%S%f")
    index_name = f"{resource_id}_{date}"
    logger.debug("creating index", extra={"index_name": index_name, "body": body})
    result = os_client.indices.create(index=index_name, body=body)

    if call_create_alias:
        # create an alias so we can interact with the index using resource_id
        create_alias(resource_id, index_name)

    if "error" in result:
        logger.error(
            "failed to create index",
            extra={"index_name": index_name, "body": body},
        )
        raise RuntimeError("failed to create index")
    logger.info("index created")
    return index_name


def create_alias(resource_id, index_name):
    if os_client.indices.exists_alias(name=resource_id):
        os_client.indices.delete_alias(name=resource_id, index="*")
    os_client.indices.put_alias(name=resource_id, index=index_name)


def refresh_index(index_name: str):
    os_client.indices.refresh(index=index_name)


def delete_index(resource_id: str):
    try:
        index_name = os_client.indices.get_alias(name=resource_id).popitem()[0]
        os_client.indices.delete(index=index_name)
    except NotFoundError:
        pass


def add_entries(resource_id: str, entries: Iterable[IndexEntry]):
    """
    Add entries using OpenSearch bulk edit API.

    Does not refresh, do it manually with refresh_index.
    """
    gen = add_entries_gen(resource_id, entries)
    # exhaust the generator before returning
    list(gen)


def add_entries_gen(resource_id: str, entries: Iterable[IndexEntry]):
    """
    Add entries using OpenSearch bulk edit API.

    Returns a generator that must be exhausted to make all edits happen.

    Does not refresh, do it manually with refresh_index.
    """
    index_to_es = (
        {
            "_index": resource_id,
            "_id": entry.id,
            "_source": entry.entry,
        }
        for entry in entries
    )

    try:
        for _ in opensearchpy.helpers.streaming_bulk(os_client, index_to_es, refresh=False):
            yield
    except opensearchpy.helpers.BulkIndexError as e:
        message = [
            "Error inserting data into Elasticsearch. The following errors occured (terminated at 400 characters):"
        ]
        for error in e.errors:
            message.append(str(error["index"])[0:400])
            raise KarpError("\n".join(message)) from None


def delete_entries(resource_id: str, *, entry_ids: Iterable[str], raise_on_error=True) -> dict[str, Any]:
    index_to_es = (
        {
            "_op_type": "delete",
            "_index": resource_id,
            "_id": str(entry_id),
        }
        for entry_id in entry_ids
    )
    _, errors = opensearchpy.helpers.bulk(os_client, index_to_es, refresh=True, raise_on_error=raise_on_error)
    return [error["delete"] for error in errors]


@dataclass
class IndexDesc:
    name: str = "missing"
    current: bool = False
    size: str = "-"


def get_indices_data(resource_ids: list[str], only_aliased=False) -> dict[str, list[IndexDesc]]:
    """
    Returns the indices associated with each given resource id. It checks if an exact alias
    exists and returns only that index if only_aliased is True. Otherwise uses regexp matching
    to find all the indices of the resource id.

    If index is completely missing, returns resource_id: list[IndexDesc()] which has name="missing",current=False,size="-"
    """

    def _get_sizes_for_indices():
        sizes = {}
        cat_indices = os_client.cat.indices(h="index,store.size", format="json")
        for row in cat_indices:
            sizes[row["index"]] = row["store.size"]
        return sizes

    def _get_alias_to_index():
        res = {}
        aliases = os_client.indices.get_alias()
        for index, alias_body in aliases.items():
            if alias_body["aliases"]:
                alias = list(alias_body["aliases"].keys())
                if len(alias) > 1:
                    raise RuntimeError(f"Index {index} has multiple aliases: {', '.join(alias)}")
                res[alias[0]] = index
        return res

    sizes = _get_sizes_for_indices()
    aliases = _get_alias_to_index()

    resource_id_to_indices = defaultdict(list)
    for resource_id in resource_ids:
        if only_aliased:
            index = aliases.get(resource_id)
            if index:
                index_desc = IndexDesc(name=index, size=str(sizes.get(index)), current=True)
            else:
                index_desc = IndexDesc()
            resource_id_to_indices[resource_id] = [index_desc]
        else:
            tmp = defaultdict(list)
            for index in sizes.keys():
                derived_alias = re.split(r"_[0-9]{4}-[0-9]{2}", index)[0]
                tmp[derived_alias].append(index)
            for index_name in tmp[resource_id]:
                current = aliases.get(resource_id) == index_name
                index_desc = IndexDesc(name=index_name, current=current, size=str(sizes.get(index)))
                resource_id_to_indices[resource_id].append(index_desc)

            if resource_id_to_indices.get(resource_id) is None:
                resource_id_to_indices[resource_id] = [IndexDesc()]

    return resource_id_to_indices


def _create_es_mapping(config):
    es_mapping = {"dynamic": False, "properties": {}}

    fields = config.fields

    def recursive_field(parent_schema, parent_field_name, parent_field_def):
        source_exclude_fields = []
        if parent_field_def.type != "object":
            # TODO this will not work when we have user defined types, s.a. saldoid
            # TODO number can be float/non-float, strings can be keyword or text in need of analyzing etc.
            if parent_field_def.type == "dense_vector":
                result = {
                    "type": "knn_vector",
                    "dimension": 768,
                    "method": {
                        "engine": "faiss",
                        "name": "hnsw",
                        "space_type": "cosinesimil",
                        "parameters": {
                            "ef_search": 500,
                        },
                    },
                }
            else:
                if parent_field_def.type == "integer":
                    mapped_type = "long"
                elif parent_field_def.type == "number":
                    mapped_type = "double"
                elif parent_field_def.type == "boolean":
                    mapped_type = "boolean"
                elif parent_field_def.type == "string":
                    mapped_type = "text"
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
