import logging
import re
import json
from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime

import elasticsearch
import elasticsearch_dsl as es_dsl  # pyre-ignore
import elasticsearch.helpers  # pyre-ignore

# from karp.query_dsl import basic_ast as ast, op, is_a

# from karp import query_dsl
from karp.domain import index
from karp.domain.models.entry import Entry
from karp.domain.models.resource import Resource
from karp.domain.errors import (
    UnsupportedField,
    # IncompleteQuery,
    # UnsupportedQuery,
)
from .es_query import EsQuery
from . import es_config

logger = logging.getLogger("karp")


class Es6Index(index.Index, index_type="es6_index"):
    def __init__(self, es: Optional[elasticsearch.Elasticsearch] = None):
        if es is None:
            logger.info(
                "Connecting to Elasticsearch with url=%s", es_config.ELASTICSEARCH_HOST
            )
            es = elasticsearch.Elasticsearch(
                hosts=es_config.ELASTICSEARCH_HOST,
                sniff_on_start=True,
                sniff_on_connection_fail=True,
                sniffer_timeout=60,
                sniff_timeout=10,
            )
        self.es: elasticsearch.Elasticsearch = es
        analyzed_fields, sortable_fields = self._init_field_mapping()
        self.analyzed_fields: Dict[str, List[str]] = analyzed_fields
        self.sortable_fields: Dict[str, Dict[str, List[str]]] = sortable_fields

    def create_index(self, resource_id, config):
        print("creating es mapping ...")
        mapping = _create_es_mapping(config)

        properties = mapping["properties"]
        properties["freetext"] = {"type": "text"}
        disabled_property = {"enabled": False}
        properties["_entry_version"] = disabled_property
        properties["_last_modified"] = disabled_property
        properties["_last_modified_by"] = disabled_property

        body = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 1,
                "refresh_interval": -1,
            },
            "mappings": {"entry": mapping},
        }

        date = datetime.now().strftime("%Y-%m-%d-%H%M%S%f")
        index_name = resource_id + "_" + date
        print(f"creating index '{index_name}' ...")
        result = self.es.indices.create(index=index_name, body=body)
        if "error" in result:
            print("failed to create index")
            raise RuntimeError("failed to create index")
        print("index created")
        return index_name

    def publish_index(self, alias_name: str, index_name: str):
        if self.es.indices.exists_alias(name=alias_name):
            self.es.indices.delete_alias(name=alias_name, index="*")

        self.on_publish_resource(alias_name, index_name)
        print(f"publishing '{alias_name}' => '{index_name}'")
        self.es.indices.put_alias(name=alias_name, index=index_name)

    def add_entries(self, index_name: str, entries: List[index.IndexEntry]):
        index_to_es = []
        for entry in entries:
            assert isinstance(entry, index.IndexEntry)
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
        self.es.delete(
            index=resource_id,
            doc_type="entry",
            id=entry_id,
            refresh=True,
        )

    @staticmethod
    def get_analyzed_fields_from_mapping(
        properties: Dict[str, Dict[str, Dict[str, Any]]]
    ) -> List[str]:
        analyzed_fields = []

        for prop_name, prop_values in properties.items():
            if "properties" in prop_values:
                res = Es6Index.get_analyzed_fields_from_mapping(
                    prop_values["properties"]
                )
                analyzed_fields.extend([prop_name + "." + prop for prop in res])
            else:
                if prop_values["type"] == "text":
                    analyzed_fields.append(prop_name)
        return analyzed_fields

    def _init_field_mapping(
        self,
    ) -> Tuple[Dict[str, List[str]], Dict[str, Dict[str, List[str]]]]:
        """
        Create a field mapping based on the mappings of elasticsearch
        currently the only information we need is if a field is analyzed (i.e. text)
        or not.
        """

        field_mapping: Dict[str, List[str]] = {}
        sortable_fields = {}
        # Doesn't work for tests, can't find resource_definition
        # for resource in resourcemgr.get_available_resources():
        #     mapping = self.es.indices.get_mapping(index=resource.resource_id)
        #     field_mapping[resource.resource_id] = parse_mapping(
        #         next(iter(mapping.values()))['mappings']['entry']['properties']
        #     )
        aliases = self._get_all_aliases()
        mapping: Dict[
            str, Dict[str, Dict[str, Dict[str, Dict]]]
        ] = self.es.indices.get_mapping()
        # print(f"mapping = {mapping}")
        for (alias, index) in aliases:
            if (
                "mappings" in mapping[index]
                and "entry" in mapping[index]["mappings"]
                and "properties" in mapping[index]["mappings"]["entry"]
            ):
                field_mapping[alias] = Es6Index.get_analyzed_fields_from_mapping(
                    mapping[index]["mappings"]["entry"]["properties"]
                )
                sortable_fields[alias] = Es6Index.create_sortable_map_from_mapping(
                    mapping[index]["mappings"]["entry"]["properties"]
                )
        return field_mapping, sortable_fields

    def _get_index_mappings(
        self, index: Optional[str] = None
    ) -> Dict[str, Dict[str, Dict[str, Dict[str, Dict]]]]:
        kwargs = {"index": index} if index is not None else {}
        return self.es.indices.get_mapping(**kwargs)

    def _get_all_aliases(self) -> List[Tuple[str, str]]:
        """
        :return: a list of tuples (alias_name, index_name)
        """
        result = self.es.cat.aliases(h="alias,index")
        print(f"{result}")
        index_names = []
        for index_name in result.split("\n")[:-1]:
            print(f"index_name = {index_name}")
            if index_name[0] != ".":
                groups = re.search(r"([^ ]*) +(.*)", index_name).groups()
                alias = groups[0]
                index = groups[1]
                index_names.append((alias, index))
        return index_names

    def build_query(self, args, resource_str: str) -> EsQuery:
        query = EsQuery()
        query.parse_arguments(args, resource_str)
        return query

    def _format_result(self, resource_ids, response):
        def format_entry(entry):
            dict_entry = entry.to_dict()
            version = dict_entry.pop("_entry_version", None)
            last_modified_by = dict_entry.pop("_last_modified_by", None)
            last_modified = dict_entry.pop("_last_modified", None)
            return {
                "id": entry.meta.id,
                "version": version,
                "last_modified": last_modified,
                "last_modified_by": last_modified_by,
                "resource": next(
                    resource
                    for resource in resource_ids
                    if entry.meta.index.startswith(resource)
                ),
                "entry": dict_entry,
            }

        result = {
            "total": response.hits.total,
            "hits": [format_entry(entry) for entry in response],
        }
        return result

    def query(self, request: index.QueryRequest):
        query = EsQuery.from_query_request(request)
        return self.search_with_query(query)

    def search_with_query(self, query: EsQuery):
        logger.info("search_with_query called with query={}".format(query))
        print("search_with_query called with query={}".format(query))
        if query.split_results:
            ms = es_dsl.MultiSearch(using=self.es)

            for resource in query.resources:
                s = es_dsl.Search(index=resource)

                if query.query is not None:
                    s = s.query(query.query)
                s = s[query.from_ : query.from_ + query.size]
                if query.sort:
                    s = s.sort(*self.translate_sort_fields([resource], query.sort))
                elif resource in query.sort_dict:
                    s = s.sort(
                        *self.translate_sort_fields(
                            [resource], query.sort_dict[resource]
                        )
                    )
                ms = ms.add(s)

            responses = ms.execute()
            result = {"total": 0, "hits": {}}
            for i, response in enumerate(responses):
                result["hits"][query.resources[i]] = self._format_result(
                    query.resources, response
                ).get("hits", [])
                result["total"] += response.hits.total
                if query.lexicon_stats:
                    if "distribution" not in result:
                        result["distribution"] = {}
                    result["distribution"][query.resources[i]] = response.hits.total
            return result
        else:
            s = es_dsl.Search(using=self.es, index=query.resource_str)
            if query.query is not None:
                s = s.query(query.query)

            s = s[query.from_ : query.from_ + query.size]

            if query.lexicon_stats:
                s.aggs.bucket(
                    "distribution", "terms", field="_index", size=len(query.resources)
                )
            if query.sort:
                s = s.sort(*self.translate_sort_fields(query.resources, query.sort))
            elif query.sort_dict:
                sort_fields = []
                for resource, sort in query.sort_dict.items():
                    sort_fields.extend(self.translate_sort_fields([resource], sort))
                s = s.sort(*sort_fields)
            logger.debug("s = {}".format(s.to_dict()))
            response = s.execute()

            # TODO format response in a better way, because the whole response takes up too much space in the logs
            # logger.debug('response = {}'.format(response.to_dict()))

            result = self._format_result(query.resources, response)
            if query.lexicon_stats:
                result["distribution"] = {}
                for bucket in response.aggregations.distribution.buckets:
                    key = bucket["key"]
                    value = bucket["doc_count"]
                    result["distribution"][key.rsplit("_", 1)[0]] = value

            return result

    def translate_sort_fields(
        self, resources: List[str], sort_values: List[str]
    ) -> List[str]:
        """Translate sort field to ES sort fields.

        Arguments:
            sort_values {List[str]} -- values to sort by

        Returns:
            List[str] -- values that ES can sort by.
        """
        translated_sort_fields: Set[str] = set()
        for sort_value in sort_values:
            for resource_id in resources:
                translated_sort_fields.update(
                    self.translate_sort_field(resource_id, sort_value)
                )

        return list(translated_sort_fields)

    def translate_sort_field(self, resource_id: str, sort_value: str) -> List[str]:
        if sort_value in self.sortable_fields[resource_id]:
            return self.sortable_fields[resource_id][sort_value]
        else:
            raise UnsupportedField(
                f"You can't sort by field '{sort_value}' for resource '{resource_id}'"
            )

    def search_ids(self, resource_id: str, entry_ids: str):
        logger.info(
            "Called EsSearch.search_ids(self, args, resource_id, entry_ids) with:"
        )
        logger.info("  resource_id = {}".format(resource_id))
        logger.info("  entry_ids = {}".format(entry_ids))
        entries = entry_ids.split(",")
        query = es_dsl.Q("terms", _id=entries)
        logger.debug("query = {}".format(query))
        s = es_dsl.Search(using=self.es, index=resource_id).query(query)
        logger.debug("s = {}".format(s.to_dict()))
        response = s.execute()

        return self._format_result([resource_id], response)

    def statistics(self, resource_id: str, field: str):
        s = es_dsl.Search(using=self.es, index=resource_id)
        s = s[0:0]

        if field in self.analyzed_fields[resource_id]:
            field = field + ".raw"

        logger.debug("Statistics: analyzed fields are:")
        logger.debug(json.dumps(self.analyzed_fields, indent=4))
        logger.debug(
            "Doing aggregations on resource_id: {resource_id}, on field {field}".format(
                resource_id=resource_id, field=field
            )
        )
        s.aggs.bucket("field_values", "terms", field=field, size=2147483647)
        response = s.execute()
        result = []
        for bucket in response.aggregations.field_values.buckets:
            result.append({"value": bucket["key"], "count": bucket["doc_count"]})
        return result

    def on_publish_resource(self, alias_name: str, index_name: str):
        mapping = self._get_index_mappings(index=index_name)
        if (
            "mappings" in mapping[index_name]
            and "entry" in mapping[index_name]["mappings"]
            and "properties" in mapping[index_name]["mappings"]["entry"]
        ):
            self.analyzed_fields[
                alias_name
            ] = Es6Index.get_analyzed_fields_from_mapping(
                mapping[index_name]["mappings"]["entry"]["properties"]
            )
            self.sortable_fields[
                alias_name
            ] = Es6Index.create_sortable_map_from_mapping(
                mapping[index_name]["mappings"]["entry"]["properties"]
            )

    @staticmethod
    def create_sortable_map_from_mapping(properties: Dict) -> Dict[str, List[str]]:
        sortable_map = {}

        def parse_prop_value(sort_map, base_name, prop_name, prop_value: Dict):
            if "properties" in prop_value:
                for ext_name, ext_value in prop_value["properties"].items():
                    ext_base_name = f"{base_name}.{ext_name}"
                    parse_prop_value(sort_map, ext_base_name, ext_base_name, ext_value)
                return
            if prop_value["type"] in [
                "boolean",
                "date",
                "double",
                "keyword",
                "long",
                "ip",
            ]:
                sort_map[base_name] = [prop_name]
                sort_map[prop_name] = [prop_name]
                return
            if prop_value["type"] == "text":
                if "fields" in prop_value:
                    for ext_name, ext_value in prop_value["fields"].items():
                        parse_prop_value(
                            sort_map, base_name, f"{base_name}.{ext_name}", ext_value
                        )
                return

        for prop_name, prop_value in properties.items():
            parse_prop_value(sortable_map, prop_name, prop_name, prop_value)
            # if prop_value["type"] in ["boolean", "date", "double", "keyword", "long", "ip"]:
            #     sortable_map[prop_name] = prop_name
            # if prop_value["type"] == "text":
            #     if "fields" in prop_value:

        return sortable_map


# def parse_sortable_fields(properties: Dict[str, Any]) -> Dict[str, List[str]]:
#     for prop_name, prop_value in properties.items():
#         if prop_value["type"] in ["boolean", "date", "double", "keyword", "long", "ip"]:
#             return [prop_name]


def _create_es_mapping(config):
    es_mapping = {"dynamic": False, "properties": {}}

    fields = config["fields"]

    def recursive_field(parent_schema, parent_field_name, parent_field_def):
        if parent_field_def.get("virtual", False):
            fun = parent_field_def["function"]
            if list(fun.keys())[0] == "multi_ref":
                res_object = fun["multi_ref"]["result"]
                recursive_field(parent_schema, "v_" + parent_field_name, res_object)
            if "result" in fun:
                res_object = fun["result"]
                recursive_field(parent_schema, "v_" + parent_field_name, res_object)
            return
        if parent_field_def.get("ref"):
            if "field" in parent_field_def["ref"]:
                res_object = parent_field_def["ref"]["field"]
            else:
                res_object = {}
                res_object.update(parent_field_def)
                del res_object["ref"]
            recursive_field(parent_schema, "v_" + parent_field_name, res_object)
        if parent_field_def["type"] != "object":
            # TODO this will not work when we have user defined types, s.a. saldoid
            # TODO number can be float/non-float, strings can be keyword or text in need of analyzing etc.
            if parent_field_def["type"] == "integer":
                mapped_type = "long"
            elif parent_field_def["type"] == "number":
                mapped_type = "double"
            elif parent_field_def["type"] == "string":
                mapped_type = "text"
            else:
                mapped_type = "keyword"
            result = {"type": mapped_type}
            if mapped_type == "text" and not parent_field_def.get("skip_raw", False):
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
