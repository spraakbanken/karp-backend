import json  # noqa: D100, I001
import logging
import re  # noqa: F401
from datetime import datetime  # noqa: F401
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, Union  # noqa: F401

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
    UnsupportedField,  # noqa: F401
)  # IncompleteQuery,; UnsupportedQuery,
from karp.lex.domain.entities.entry import Entry  # noqa: F401
from karp.lex.domain.entities.resource import Resource  # noqa: F401
from karp.search.domain import query_dsl
from karp.search_infrastructure.elasticsearch6 import es_config  # noqa: F401
from karp.search_infrastructure.elasticsearch6 import Es6MappingRepository
from .es_query import EsQuery

# from karp.query_dsl import basic_ast as ast, op, is_a


logger = logging.getLogger(__name__)


class EsQueryBuilder(query_dsl.NodeWalker):  # noqa: D101
    def walk_object(self, node):  # noqa: ANN201, D102, ANN001
        return node

    def walk__and(self, node):  # noqa: ANN201, D102, ANN001
        result = self.walk(node.exps[0])
        for n in node.exps[1:]:
            result = result & self.walk(n)

        return result

    def walk__contains(self, node):  # noqa: ANN201, D102, ANN001
        return es_dsl.Q(
            "regexp", **{self.walk(node.field): f".*{self.walk(node.arg)}.*"}
        )

    def walk__endswith(self, node):  # noqa: ANN201, D102, ANN001
        return es_dsl.Q("regexp", **{self.walk(node.field): f".*{self.walk(node.arg)}"})

    # def walk__equals(self, node):
    #     return es_dsl.Q(
    #         "match",
    #         **{
    #             self.walk(node.field): {"query": self.walk(node.arg), "operator": "and"}
    #         },
    #     )

    def walk__equals(self, node):  # noqa: ANN201, D102, ANN001
        return es_dsl.Q(
            "match",
            **{
                self.walk(node.field): {"query": self.walk(node.arg), "operator": "and"}
            },
        )

    def walk__exists(self, node):  # noqa: ANN201, D102, ANN001
        return es_dsl.Q("exists", field=self.walk(node.field))

    def walk__freergxp(self, node):  # noqa: ANN201, D102, ANN001
        return es_dsl.Q(
            "query_string", query=f"/{self.walk(node.arg)}/", default_field="*"
        )

    def walk__freetext_string(self, node):  # noqa: ANN201, D102, ANN001
        return es_dsl.Q("multi_match", query=self.walk(node.arg), fuzziness=1)

    def walk__freetext_any_but_string(self, node):  # noqa: ANN201, D102, ANN001
        return es_dsl.Q("multi_match", query=self.walk(node.arg))

    def walk_range(self, node):  # noqa: ANN201, D102, ANN001
        return es_dsl.Q(
            "range",
            **{self.walk(node.field): {self.walk(node.op): self.walk(node.arg)}},
        )

    walk__gt = walk_range
    walk__gte = walk_range
    walk__lt = walk_range
    walk__lte = walk_range

    def walk__missing(self, node):  # noqa: ANN201, D102, ANN001
        return es_dsl.Q(
            "bool", must_not=es_dsl.Q("exists", field=self.walk(node.field))
        )

    def walk__not(self, node):  # noqa: ANN201, D102, ANN001
        must_nots = [self.walk(expr) for expr in node.exps]
        return es_dsl.Q("bool", must_not=must_nots)

    def walk__or(self, node):  # noqa: ANN201, D102, ANN001
        result = self.walk(node.exps[0])
        for n in node.exps[1:]:
            result = result | self.walk(n)

        return result

    def walk__regexp(self, node):  # noqa: ANN201, D102, ANN001
        return es_dsl.Q("regexp", **{self.walk(node.field): self.walk(node.arg)})

    def walk__startswith(self, node):  # noqa: ANN201, D102, ANN001
        return es_dsl.Q("regexp", **{self.walk(node.field): f"{self.walk(node.arg)}.*"})


class Es6SearchService(search.SearchService):  # noqa: D101
    def __init__(  # noqa: D107, ANN204
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

    def build_query(self, args, resource_str: str) -> EsQuery:  # noqa: D102, ANN001
        query = EsQuery()
        # query.parse_arguments(args, resource_str)
        return query

    def _format_result(self, resource_ids, response):  # noqa: ANN202, ANN001
        logger.debug("_format_result called", extra={"resource_ids": resource_ids})
        resource_id_map = {
            resource_id: self.mapping_repo.get_name_base(resource_id)
            for resource_id in resource_ids
        }

        def format_entry(entry):  # noqa: ANN202, ANN001
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
                    for resource, index_base in resource_id_map.items()
                    if entry.meta.index.startswith(index_base)
                ),
                "entry": dict_entry,
            }

        result = {
            "total": response.hits.total,
            "hits": [format_entry(entry) for entry in response],
        }
        return result

    def query(self, request: QueryRequest):  # noqa: ANN201, D102
        logger.info("query called", extra={"request": request})
        query = EsQuery.from_query_request(request)
        return self.search_with_query(query)

    def query_split(self, request: QueryRequest):  # noqa: ANN201, D102
        logger.info("query_split called", extra={"request": request})
        query = EsQuery.from_query_request(request)
        query.split_results = True
        return self.search_with_query(query)

    def search_with_query(self, query: EsQuery):  # noqa: ANN201, D102, C901
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
                alias_name = self.mapping_repo.get_alias_name(resource)
                s = es_dsl.Search(index=alias_name)

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
    def _extracted_from_search_with_query_47(self, query, es_query):  # noqa: ANN202, ANN001
        alias_names = [
            self.mapping_repo.get_alias_name(resource) for resource in query.resources
        ]
        s = es_dsl.Search(using=self.es, index=alias_names, doc_type="entry")
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

    def search_ids(self, resource_id: str, entry_ids: str):  # noqa: ANN201, D102
        logger.info(
            "Called EsSearch.search_ids with:",
            extra={"resource_id": resource_id, "entry_ids": entry_ids},
        )
        entries = entry_ids.split(",")
        query = es_dsl.Q("terms", _id=entries)
        logger.debug("query", extra={"query": query})
        alias_name = self.mapping_repo.get_alias_name(resource_id)
        s = es_dsl.Search(using=self.es, index=alias_name).query(query)
        logger.debug("s", extra={"es_query s": s.to_dict()})
        response = s.execute()

        return self._format_result([resource_id], response)

    def statistics(self, resource_id: str, field: str) -> Iterable:  # noqa: D102
        alias_name = self.mapping_repo.get_alias_name(resource_id)
        s = es_dsl.Search(using=self.es, index=alias_name)
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
