import abc
from datetime import datetime
import logging
import re
from typing import Dict, List, Optional, Any, Tuple, Union

import elasticsearch
from elasticsearch import exceptions as es_exceptions

from karp.foundation.events import EventBus

from karp.lex.domain.entities import Entry
from karp.search.application.repositories import (
    Index,
    IndexEntry,
    IndexUnitOfWork,
)


logger = logging.getLogger("karp")

KARP_CONFIGINDEX = "karp_config"
KARP_CONFIGINDEX_TYPE = "configs"


class ConfigRepository(abc.ABC):
    pass


class Es6ConfigRepository(Index):
    def __init__(self, es: elasticsearch.Elasticsearch):
        self.es: elasticsearch.Elasticsearch = es
        self.ensure_config_index_exist()
        analyzed_fields, sortable_fields = self._init_field_mapping()
        self.analyzed_fields: Dict[str, List[str]] = analyzed_fields
        self.sortable_fields: Dict[str, Dict[str, List[str]]] = sortable_fields

    def ensure_config_index_exist(self) -> None:
        if not self.es.indices.exists(index=KARP_CONFIGINDEX):
            self.es.indices.create(
                index=KARP_CONFIGINDEX,
                body={
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 1,
                        "refresh_interval": -1,
                    },
                    "mappings": {
                        KARP_CONFIGINDEX_TYPE: {
                            "dynamic": False,
                            "properties": {"index_name": {"type": "text"}},
                        }
                    },
                },
            )
    @property
    def seen(self):
        return []

    def create_index(self, resource_id, config):
        print("creating es mapping ...")
        mapping = create_es6_mapping(config)

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
        self._set_index_name_for_resource(resource_id, index_name)
        return index_name

    def _set_index_name_for_resource(self, resource_id: str, index_name: str) -> str:
        self.es.index(
            index=KARP_CONFIGINDEX,
            id=resource_id,
            doc_type=KARP_CONFIGINDEX_TYPE,
            body={"index_name": index_name},
        )
        return index_name

    def _get_index_name_for_resource(self, resource_id: str) -> str:
        try:
            res = self.es.get(
                index=KARP_CONFIGINDEX, id=resource_id, doc_type=KARP_CONFIGINDEX_TYPE
            )
        except es_exceptions.NotFoundError as err:
            logger.debug(
                "didn't find index_name for resource '%s' details: %s", resource_id, err)
            return self._set_index_name_for_resource(resource_id, resource_id)
        return res["_source"]["index_name"]

    def publish_index(self, resource_id: str):
        if self.es.indices.exists_alias(name=resource_id):
            self.es.indices.delete_alias(name=resource_id, index="*")

        index_name = self._get_index_name_for_resource(resource_id)
        self.on_publish_resource(resource_id, index_name)
        print(f"publishing '{resource_id}' => '{index_name}'")
        self.es.indices.put_alias(name=resource_id, index=index_name)

    def add_entries(self, resource_id: str, entries: List[IndexEntry]):
        index_name = self._get_index_name_for_resource(resource_id)
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
                analyzed_fields.extend(
                    [prop_name + "." + prop for prop in res])
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

    def translate_sort_fields(
        self, resources: List[str], sort_values: List[str]
    ) -> List[Union[str, Dict[str, Dict[str, str]]]]:
        """Translate sort field to ES sort fields.

        Arguments:
            sort_values {List[str]} -- values to sort by

        Returns:
            List[str] -- values that ES can sort by.
        """
        translated_sort_fields: List[Union[str,
                                           Dict[str, Dict[str, str]]]] = []
        for sort_value in sort_values:
            sort_order = None
            if "|" in sort_value:
                sort_value, sort_order = sort_value.split("|", 1)
            for resource_id in resources:
                if sort_order:
                    translated_sort_fields.extend(
                        (
                            {field: {"order": sort_order}}
                            for field in self.translate_sort_field(
                                resource_id, sort_value
                            )
                        )
                    )
                translated_sort_fields.extend(
                    self.translate_sort_field(resource_id, sort_value)
                )

        return translated_sort_fields

    def translate_sort_field(self, resource_id: str, sort_value: str) -> List[str]:
        print(
            f"es6_indextranslate_sort_field: sortable_fields[{resource_id}] = {self.sortable_fields[resource_id]}"
        )
        if sort_value in self.sortable_fields[resource_id]:
            return self.sortable_fields[resource_id][sort_value]
        else:
            raise UnsupportedField(
                f"You can't sort by field '{sort_value}' for resource '{resource_id}'"
            )

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
                    parse_prop_value(sort_map, ext_base_name,
                                     ext_base_name, ext_value)
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
                recursive_field(parent_schema, "v_" +
                                parent_field_name, res_object)
            if "result" in fun:
                res_object = fun["result"]
                recursive_field(parent_schema, "v_" +
                                parent_field_name, res_object)
            return
        if parent_field_def.get("ref"):
            if "field" in parent_field_def["ref"]:
                res_object = parent_field_def["ref"]["field"]
            else:
                res_object = {}
                res_object.update(parent_field_def)
                del res_object["ref"]
            recursive_field(parent_schema, "v_" +
                            parent_field_name, res_object)
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
            elif parent_field_def['type'] == 'long_string':
                mapped_type = 'text'
            else:
                mapped_type = "keyword"
            result = {"type": mapped_type}
            if parent_field_def['type'] == 'string':
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
    mapping['settings'] = {
        'analysis': {
            'analyzer': {
                'default': {
                    'char_filter': [
                        'compound',
                        'swedish_aa',
                        'swedish_ae',
                        'swedish_oe'
                    ],
                    'filter': [
                        'swedish_folding',
                        'lowercase'
                    ],
                    'tokenizer': 'standard'
                }
            },
            'char_filter': {
                'compound': {
                    'pattern': '-',
                    'replacement': '',
                    'type': 'pattern_replace'
                },
                'swedish_aa': {
                    'pattern': '[Ǻǻ]',
                    'replacement': 'å',
                    'type': 'pattern_replace'
                },
                'swedish_ae': {
                    'pattern': '[æÆǞǟ]',
                    'replacement': 'ä',
                    'type': 'pattern_replace'
                },
                'swedish_oe': {
                    'pattern': '[ØøŒœØ̈ø̈ȪȫŐőÕõṌṍṎṏȬȭǾǿǬǭŌōṒṓṐṑ]',
                    'replacement': 'ö',
                    'type': 'pattern_replace'
                },
            },
            'filter': {
                'swedish_folding': {
                    'type': 'icu_folding',
                    'unicodeSetFilter': '[^åäöÅÄÖ]'
                },
                'swedish_sort': {
                    'language': 'sv',
                    'type': 'icu_collation'
                }
            }
        }
    }
    return mapping


class Es6IndexUnitOfWork(
    IndexUnitOfWork
):
    def __init__(
        self,
        es: elasticsearch.Elasticsearch,
        event_bus: EventBus,
    ) -> None:
        super().__init__(event_bus=event_bus)
        self._index = Es6Index(es=es)

    # @classmethod
    # def from_dict(cls, **kwargs):
    #     return cls()

    def _commit(self):
        logger.debug('Calling _commit in Es6IndexUnitOfWork')

    def rollback(self):
        return super().rollback()

    @property
    def repo(self) -> Es6Index:
        return self._index

    def _close(self):
        pass
import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import elasticsearch
import elasticsearch.helpers  # pyre-ignore
import elasticsearch_dsl as es_dsl  # pyre-ignore

# from karp import query_dsl
from karp.search.application.queries import (
    QueryRequest,
    SearchService,
)
from karp.search.domain.errors import \
    UnsupportedField  # IncompleteQuery,; UnsupportedQuery,
from karp.lex.domain.entities.entry import Entry
from karp.lex.domain.entities.resource import Resource
from karp.search.domain import query_dsl
from karp.search_infrastructure.elasticsearch6 import es_config
from .es_query import EsQuery

# from karp.query_dsl import basic_ast as ast, op, is_a


logger = logging.getLogger("karp")

KARP_CONFIGINDEX = "karp_config"
KARP_CONFIGINDEX_TYPE = "configs"


class EsQueryBuilder(query_dsl.NodeWalker):
    def walk_object(self, node):
        return node

    def walk__and(self, node):
        result = self.walk(node.exps[0])
        for n in node.exps[1:]:
            result = result & self.walk(n)

        return result

    def walk__contains(self, node):
        return es_dsl.Q(
            "regexp", **{self.walk(node.field): f".*{self.walk(node.arg)}.*"}
        )

    def walk__endswith(self, node):
        return es_dsl.Q("regexp", **{self.walk(node.field): f".*{self.walk(node.arg)}"})

    # def walk__equals(self, node):
    #     return es_dsl.Q(
    #         "match",
    #         **{
    #             self.walk(node.field): {"query": self.walk(node.arg), "operator": "and"}
    #         },
    #     )

    def walk__equals(self, node):
        return es_dsl.Q(
            "match",
            **{self.walk(node.field): {"query": self.walk(node.arg), "operator": "and"}}
        )

    def walk__exists(self, node):
        return es_dsl.Q("exists", field=self.walk(node.field))

    def walk__freergxp(self, node):
        return es_dsl.Q(
            "query_string", query=f"/{self.walk(node.arg)}/", default_field="*"
        )

    def walk__freetext_string(self, node):
        return es_dsl.Q("multi_match", query=self.walk(node.arg), fuzziness=1)

    def walk__freetext_any_but_string(self, node):
        return es_dsl.Q("multi_match", query=self.walk(node.arg))

    def walk_range(self, node):
        return es_dsl.Q(
            "range",
            **{self.walk(node.field): {self.walk(node.op): self.walk(node.arg)}},
        )

    walk__gt = walk_range
    walk__gte = walk_range
    walk__lt = walk_range
    walk__lte = walk_range

    def walk__missing(self, node):
        return es_dsl.Q(
            "bool", must_not=es_dsl.Q("exists", field=self.walk(node.field))
        )

    def walk__not(self, node):
        return ~self.walk(node.expr)

    def walk__or(self, node):
        result = self.walk(node.exps[0])
        for n in node.exps[1:]:
            result = result | self.walk(n)

        return result

    def walk__regexp(self, node):
        return es_dsl.Q("regexp", **{self.walk(node.field): self.walk(node.arg)})

    def walk__startswith(self, node):
        return es_dsl.Q("regexp", **{self.walk(node.field): f"{self.walk(node.arg)}.*"})


class Es6SearchService(SearchService):
    def __init__(self, es: elasticsearch.Elasticsearch):
        self.es: elasticsearch.Elasticsearch = es
        self.query_builder = EsQueryBuilder()
        self.parser = query_dsl.KarpQueryV6Parser(
            semantics=query_dsl.KarpQueryV6ModelBuilderSemantics())
        if not self.es.indices.exists(index=KARP_CONFIGINDEX):
            self.es.indices.create(
                index=KARP_CONFIGINDEX,
                body={
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 1,
                        "refresh_interval": -1,
                    },
                    "mappings": {
                        KARP_CONFIGINDEX_TYPE: {
                            "dynamic": False,
                            "properties": {"index_name": {"type": "text"}},
                        }
                    },
                },
            )
        analyzed_fields, sortable_fields = self._init_field_mapping()
        self.analyzed_fields: Dict[str, List[str]] = analyzed_fields
        self.sortable_fields: Dict[str, Dict[str, List[str]]] = sortable_fields

    def _get_index_name_for_resource(self, resource_id: str) -> str:
        res = self.es.get(
            index=KARP_CONFIGINDEX, id=resource_id, doc_type=KARP_CONFIGINDEX_TYPE
        )
        return res["_source"]["index_name"]

    @staticmethod
    def get_analyzed_fields_from_mapping(
        properties: Dict[str, Dict[str, Dict[str, Any]]]
    ) -> List[str]:
        analyzed_fields = []

        for prop_name, prop_values in properties.items():
            if "properties" in prop_values:
                res = Es6SearchService.get_analyzed_fields_from_mapping(
                    prop_values["properties"]
                )
                analyzed_fields.extend(
                    [prop_name + "." + prop for prop in res])
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
                field_mapping[alias] = Es6SearchService.get_analyzed_fields_from_mapping(
                    mapping[index]["mappings"]["entry"]["properties"]
                )
                sortable_fields[alias] = Es6SearchService.create_sortable_map_from_mapping(
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
        logger.debug(
            "es6_search_service_format_result called with resource_ids=%s", resource_ids
        )

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

    def query(self, request: QueryRequest):
        print(f"query called with {request}")
        query = EsQuery.from_query_request(request)
        return self.search_with_query(query)

    def query_split(self, request: QueryRequest):
        print(f"query called with {request}")
        query = EsQuery.from_query_request(request)
        query.split_results = True
        return self.search_with_query(query)

    def search_with_query(self, query: EsQuery):
        logger.info("search_with_query called with query=%s", query)
        print("search_with_query called with query={}".format(query))
        es_query = None
        if query.q:
            model = self.parser(query.q)
            es_query = self.query_builder.walk(model)
        if query.split_results:
            ms = es_dsl.MultiSearch(using=self.es)

            for resource in query.resources:
                s = es_dsl.Search(index=resource)

                if es_query is not None:
                    s = s.query(es_query)
                s = s[query.from_: query.from_ + query.size]
                if query.sort:
                    s = s.sort(
                        *self.translate_sort_fields([resource], query.sort))
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
                    result["distribution"][query.resources[i]
                                           ] = response.hits.total
            return result
        else:
            s = es_dsl.Search(
                using=self.es, index=query.resources, doc_type="entry")
            if es_query is not None:
                s = s.query(es_query)

            s = s[query.from_: query.from_ + query.size]

            if query.lexicon_stats:
                s.aggs.bucket(
                    "distribution", "terms", field="_index", size=len(query.resources)
                )
            if query.sort:
                s = s.sort(
                    *self.translate_sort_fields(query.resources, query.sort))
            elif query.sort_dict:
                sort_fields = []
                for resource, sort in query.sort_dict.items():
                    sort_fields.extend(
                        self.translate_sort_fields([resource], sort))
                s = s.sort(*sort_fields)
            logger.debug("s = %s", s.to_dict())
            response = s.execute()

            # TODO format response in a better way, because the whole response takes up too much space in the logs
            # logger.debug('response = {}'.format(response.to_dict()))

            logger.debug("calling _format_result")
            result = self._format_result(query.resources, response)
            if query.lexicon_stats:
                result["distribution"] = {}
                for bucket in response.aggregations.distribution.buckets:
                    key = bucket["key"]
                    value = bucket["doc_count"]
                    result["distribution"][key.rsplit("_", 1)[0]] = value

            # logger.debug("return result = %s", result)
            return result

    def translate_sort_fields(
        self, resources: List[str], sort_values: List[str]
    ) -> List[Union[str, Dict[str, Dict[str, str]]]]:
        """Translate sort field to ES sort fields.

        Arguments:
            sort_values {List[str]} -- values to sort by

        Returns:
            List[str] -- values that ES can sort by.
        """
        translated_sort_fields: List[Union[str,
                                           Dict[str, Dict[str, str]]]] = []
        for sort_value in sort_values:
            sort_order = None
            if "|" in sort_value:
                sort_value, sort_order = sort_value.split("|", 1)
            for resource_id in resources:
                if sort_order:
                    translated_sort_fields.extend(
                        (
                            {field: {"order": sort_order}}
                            for field in self.translate_sort_field(
                                resource_id, sort_value
                            )
                        )
                    )
                translated_sort_fields.extend(
                    self.translate_sort_field(resource_id, sort_value)
                )

        return translated_sort_fields

    def translate_sort_field(self, resource_id: str, sort_value: str) -> List[str]:
        print(
            f"es6_search_servicetranslate_sort_field: sortable_fields[{resource_id}] = {self.sortable_fields[resource_id]}"
        )
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
            field += ".raw"

        logger.debug("Statistics: analyzed fields are:")
        logger.debug(json.dumps(self.analyzed_fields, indent=4))
        logger.debug(
            "Doing aggregations on resource_id: {resource_id}, on field {field}".format(
                resource_id=resource_id, field=field
            )
        )
        s.aggs.bucket("field_values", "terms", field=field, size=2147483647)
        response = s.execute()
        print(f'{response=}')
        return [
            {"value": bucket["key"], "count": bucket["doc_count"]}
            for bucket in response.aggregations.field_values.buckets
        ]

    def on_publish_resource(self, alias_name: str, index_name: str):
        mapping = self._get_index_mappings(index=index_name)
        if (
            "mappings" in mapping[index_name]
            and "entry" in mapping[index_name]["mappings"]
            and "properties" in mapping[index_name]["mappings"]["entry"]
        ):
            self.analyzed_fields[
                alias_name
            ] = Es6SearchService.get_analyzed_fields_from_mapping(
                mapping[index_name]["mappings"]["entry"]["properties"]
            )
            self.sortable_fields[
                alias_name
            ] = Es6SearchService.create_sortable_map_from_mapping(
                mapping[index_name]["mappings"]["entry"]["properties"]
            )

    @staticmethod
    def create_sortable_map_from_mapping(properties: Dict) -> Dict[str, List[str]]:
        sortable_map = {}

        def parse_prop_value(sort_map, base_name, prop_name, prop_value: Dict):
            if "properties" in prop_value:
                for ext_name, ext_value in prop_value["properties"].items():
                    ext_base_name = f"{base_name}.{ext_name}"
                    parse_prop_value(sort_map, ext_base_name,
                                     ext_base_name, ext_value)
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



