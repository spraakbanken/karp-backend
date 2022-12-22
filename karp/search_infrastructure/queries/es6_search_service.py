import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, Union

import elasticsearch
import elasticsearch.helpers  # pyre-ignore
import elasticsearch_dsl as es_dsl  # pyre-ignore
from tatsu import exceptions as tatsu_exc

from karp import search

# from karp import query_dsl
from karp.search.application.queries import (
    QueryRequest,
)
from karp.search.domain import errors
from karp.search.domain.errors import (
    UnsupportedField,
)  # IncompleteQuery,; UnsupportedQuery,
from karp.lex.domain.entities.entry import Entry
from karp.lex.domain.entities.resource import Resource
from karp.search.domain import query_dsl
from karp.search_infrastructure.elasticsearch6 import es_config
from karp.search_infrastructure.elasticsearch6 import Es6MappingRepository
from .es_query import EsQuery

# from karp.query_dsl import basic_ast as ast, op, is_a


logger = logging.getLogger(__name__)


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
            **{
                self.walk(node.field): {"query": self.walk(node.arg), "operator": "and"}
            },
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
        must_nots = [self.walk(expr) for expr in node.exps]
        return es_dsl.Q("bool", must_not=must_nots)

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
    def __init__(
        self,
        es: elasticsearch.Elasticsearch,
        mapping_repo: Es6MappingRepository,
    ):
        self.es: elasticsearch.Elasticsearch = es
        self.mapping_repo = mapping_repo
        self.query_builder = EsQueryBuilder()
        self.parser = query_dsl.KarpQueryV6Parser(
            semantics=query_dsl.KarpQueryV6ModelBuilderSemantics()
        )

    def build_query(self, args, resource_str: str) -> EsQuery:
        query = EsQuery()
        query.parse_arguments(args, resource_str)
        return query

    def _format_result(self, resource_ids, response):
        logger.debug("_format_result called", extra={"resource_ids": resource_ids})

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
        logger.info("query called", extra={"request": request})
        query = EsQuery.from_query_request(request)
        return self.search_with_query(query)

    def query_split(self, request: QueryRequest):
        logger.info("query_split called", extra={"request": request})
        query = EsQuery.from_query_request(request)
        query.split_results = True
        return self.search_with_query(query)

    def search_with_query(self, query: EsQuery):
        logger.info("search_with_query called", extra={"query": query})
        es_query = None
        if query.q:
            try:
                model = self.parser.parse(query.q)
                es_query = self.query_builder.walk(model)
            except tatsu_exc.FailedParse as err:
                logger.debug("Parse error", extra={"err": err})
                raise errors.IncompleteQuery(
                    failing_query=query.q, error_description=str(err)
                ) from err
        if query.split_results:
            ms = es_dsl.MultiSearch(using=self.es)

            for resource in query.resources:
                s = es_dsl.Search(index=resource)

                if es_query is not None:
                    s = s.query(es_query)
                s = s[query.from_ : query.from_ + query.size]
                if query.sort:
                    s = s.sort(
                        *self.mapping_repo.translate_sort_fields([resource], query.sort)
                    )
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
                    result["distribution"][query.resources[i]] = response.hits.total
        else:
            result = self._extracted_from_search_with_query_47(query, es_query)

        return result

    # TODO Rename this here and in `search_with_query`
    def _extracted_from_search_with_query_47(self, query, es_query):
        s = es_dsl.Search(using=self.es, index=query.resources, doc_type="entry")
        if es_query is not None:
            s = s.query(es_query)

        s = s[query.from_ : query.from_ + query.size]

        if query.lexicon_stats:
            s.aggs.bucket(
                "distribution", "terms", field="_index", size=len(query.resources)
            )
        if query.sort:
            s = s.sort(
                *self.mapping_repo.translate_sort_fields(query.resources, query.sort)
            )
        elif query.sort_dict:
            sort_fields = []
            for resource, sort in query.sort_dict.items():
                sort_fields.extend(
                    self.mapping_repo.translate_sort_fields([resource], sort)
                )
            s = s.sort(*sort_fields)
        logger.debug("s = %s", extra={"es_query s": s.to_dict()})
        response = s.execute()

        # TODO format response in a better way, because the whole response takes up too much space in the logs
        # logger.debug('response = {}'.format(response.to_dict()))

        logger.debug("calling _format_result")
        result = self._format_result(query.resources, response)
        if query.lexicon_stats:
            result["distribution"] = {}
            for bucket in response.aggregations.distribution.buckets:
                key = bucket["key"]
                result["distribution"][key.rsplit("_", 1)[0]] = bucket["doc_count"]

        return result

    def search_ids(self, resource_id: str, entry_ids: str):
        logger.info(
            "Called EsSearch.search_ids with:",
            extra={"resource_id": resource_id, "entry_ids": entry_ids},
        )
        entries = entry_ids.split(",")
        query = es_dsl.Q("terms", _id=entries)
        logger.debug("query", extra={"query": query})
        s = es_dsl.Search(using=self.es, index=resource_id).query(query)
        logger.debug("s", extra={"es_query s": s.to_dict()})
        response = s.execute()

        return self._format_result([resource_id], response)

    def statistics(self, resource_id: str, field: str) -> Iterable:
        s = es_dsl.Search(using=self.es, index=resource_id)
        s = s[:0]

        if field in self.mapping_repo.analyzed_fields[resource_id]:
            field += ".raw"

        logger.debug("Statistics: analyzed fields are:")
        logger.debug(json.dumps(self.mapping_repo.analyzed_fields, indent=4))
        logger.debug(
            "Doing aggregations on resource_id: {resource_id}, on field {field}".format(
                resource_id=resource_id, field=field
            )
        )
        s.aggs.bucket("field_values", "terms", field=field, size=2147483647)
        response = s.execute()
        logger.debug("Elasticsearch response", extra={"response": response})
        return [
            {"value": bucket["key"], "count": bucket["doc_count"]}
            for bucket in response.aggregations.field_values.buckets
        ]
