import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, Union

import elasticsearch
import elasticsearch.helpers  # pyre-ignore
import elasticsearch_dsl as es_dsl  # pyre-ignore
import logging
from tatsu import exceptions as tatsu_exc

from karp import search
# from karp import query_dsl
from karp.search.application.queries import (
    QueryRequest,
    SearchService,
)
from karp.search.domain import errors
from karp.search.domain.errors import \
    UnsupportedField  # IncompleteQuery,; UnsupportedQuery,
from karp.lex.domain.entities.entry import Entry
from karp.lex.domain.entities.resource import Resource
from karp.search.domain import query_dsl
from karp.search_infrastructure.elasticsearch6 import es_config
from .es_query import EsQuery

# from karp.query_dsl import basic_ast as ast, op, is_a


logger = logging.getLogger(__name__)

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


class Es6SearchService(search.SearchService):
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
        logger.debug('ES aliases and indicies', extra={'result': result})
        index_names = []
        for index_name in result.split("\n")[:-1]:
            logger.debug('existing index', extra={'index_name': index_name})
            if index_name[0] != ".":
                opt_match = re.search(r"([^ ]*) +(.*)", index_name)
                if opt_match:
                    groups = opt_match.groups()
                    alias = groups[0]
                    index = groups[1]
                    index_names.append((alias, index))
        return index_names

    def build_query(self, args, resource_str: str) -> EsQuery:
        query = EsQuery()
        query.parse_arguments(args, resource_str)
        return query

    def _format_result(self, resource_ids, response):
        logger.debug('_format_result called', extra={
                     'resource_ids': resource_ids})

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
        logger.info('query called', extra={'request': request})
        query = EsQuery.from_query_request(request)
        return self.search_with_query(query)

    def query_split(self, request: QueryRequest):
        logger.info('query_split called', extra={'request': request})
        query = EsQuery.from_query_request(request)
        query.split_results = True
        return self.search_with_query(query)

    def search_with_query(self, query: EsQuery):
        logger.info('search_with_query called', extra={'query': query})
        es_query = None
        if query.q:
            try:
                model = self.parser.parse(query.q)
                es_query = self.query_builder.walk(model)
            except tatsu_exc.FailedParse as err:
                logger.debug('Parse error', extra={'err': err})
                raise errors.IncompleteQuery(
                    failing_query=query.q,
                    error_description=str(err)
                ) from err
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
                elif query.sort_dict and resource in query.sort_dict:
                    s = s.sort(
                        *self.translate_sort_fields(
                            [resource], query.sort_dict[resource]
                        )
                    )
                ms = ms.add(s)

            responses = ms.execute()
            result: dict[str, Any] = {"total": 0, "hits": {}}
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
            logger.debug("s = %s", extra={'es_query s': s.to_dict()})
            response = s.execute()

            # TODO format response in a better way, because the whole response takes up too much space in the logs
            # logger.debug('response = {}'.format(response.to_dict()))

            logger.debug('calling _format_result')
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
        logger.debug(
            'sortable fields for resource', extra={'resource_id': resource_id, 'sortable_fields': self.sortable_fields[resource_id]}
        )
        if sort_value in self.sortable_fields[resource_id]:
            return self.sortable_fields[resource_id][sort_value]
        else:
            raise UnsupportedField(
                f"You can't sort by field '{sort_value}' for resource '{resource_id}'"
            )

    def search_ids(self, resource_id: str, entry_ids: str):
        logger.info(
            'Called EsSearch.search_ids with:', extra={
                'resource_id': resource_id,
                'entry_ids': entry_ids})
        entries = entry_ids.split(",")
        query = es_dsl.Q("terms", _id=entries)
        logger.debug('query', extra={'query': query})
        s = es_dsl.Search(using=self.es, index=resource_id).query(query)
        logger.debug('s', extra={'es_query s': s.to_dict()})
        response = s.execute()

        return self._format_result([resource_id], response)

    def statistics(self, resource_id: str, field: str) -> Iterable:
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
        logger.debug('Elasticsearch response', extra={'response': response})
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
    def create_sortable_map_from_mapping(properties: dict) -> dict[str, list[str]]:
        sortable_map: dict[str, list[str]] = {}

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
