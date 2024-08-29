import logging
from itertools import groupby
from typing import Any, Dict, Iterable, List, Optional

import elasticsearch
import elasticsearch.helpers
import elasticsearch_dsl as es_dsl
from injector import inject
from tatsu import exceptions as tatsu_exc
from tatsu.walkers import NodeWalker

from karp.foundation.json import get_path
from karp.main.errors import KarpError
from karp.search.domain import QueryRequest, errors
from karp.search.domain.query_dsl.karp_query_v6_model import (
    KarpQueryV6ModelBuilderSemantics,
)
from karp.search.domain.query_dsl.karp_query_v6_parser import KarpQueryV6Parser

from .mapping_repo import EsMappingRepository

logger = logging.getLogger(__name__)


class EsQueryBuilder(NodeWalker):
    def __init__(self, resources, mapping_repo, q=None):
        super().__init__()
        self._q = q
        self.path = ""
        self.resources = resources
        self.mapping_repo = mapping_repo

    def walk__equals(self, node):
        return self.match(node.field, self.walk(node.arg))

    def walk__freetext(self, node):
        return self.match("*", self.walk(node.arg))

    def walk__regexp(self, node):
        return self.regexp(node.field, self.walk(node.arg))

    def walk__freergxp(self, node):
        return self.regexp("*", self.walk(node.arg))

    def walk__contains(self, node):
        return self.regexp(node.field, f".*{self.walk(node.arg)}.*")

    def walk__startswith(self, node):
        return self.regexp(node.field, f"{self.walk(node.arg)}.*")

    def walk__endswith(self, node):
        return self.regexp(node.field, f".*{self.walk(node.arg)}")

    def walk__exists(self, node):
        def query_f(field):
            return es_dsl.Q("exists", field=field)

        return self._exists_missing_range_helper("exists", node, query_f)

    def walk__missing(self, node):
        def query_f(field):
            return es_dsl.Q("bool", must_not=es_dsl.Q("exists", field=field))

        return self._exists_missing_range_helper("missing", node, query_f)

    def walk_range(self, node):
        def query_f(field):
            return es_dsl.Q("range", **{field: {self.walk(node.op): self.walk(node.arg)}})

        return self._exists_missing_range_helper(node.op, node, query_f)

    walk__gt = walk_range
    walk__gte = walk_range
    walk__lt = walk_range
    walk__lte = walk_range

    def walk__not(self, node):
        must_nots = [self.walk(expr) for expr in node.ast]
        return es_dsl.Q("bool", must_not=must_nots)

    def walk__or(self, node):
        result = self.walk(node.ast[0])
        for n in node.ast[1:]:
            result = result | self.walk(n)

        return result

    def walk__and(self, node):
        result = self.walk(node.ast[0])
        for n in node.ast[1:]:
            result = result & self.walk(n)

        return result

    def walk__sub_query(self, node):
        path = self.walk(node.field)
        self.path = path + "."
        query = self.walk(node.exp)
        self.path = ""
        # add ".TODO" to path since wrap_nested splits, refactor!
        return self.wrap_nested(path + ".TODO", query)

    def wrap_nested(self, field, query):
        path, *leaf = field.rsplit(".", 1)

        # if leaf is empty, the field is not a path, and cannot be nested
        if not leaf:
            return query

        # if self.path is set and the current field is part of the current path, no nesting should be added at this level
        # TODO ugly, refactor
        if self.path and (path + ".") == self.path:
            pass
        else:
            # check that all the resources have the same nested settings for the field, if they do not, the query will fail
            g = groupby(
                [
                    self.mapping_repo.is_nested(resource_id, self.path + path)
                    for resource_id in self.resources
                ]
            )
            is_nested = next(g)[0]
            if next(g, False):
                raise errors.IncompleteQuery(
                    self._q,
                    f"Resources: {self.resources} have different settings for field: {self.path + field}",
                )

            if is_nested:
                query = es_dsl.Q("nested", path=path, query=query)

        # check if there are most nested fields in the remaining path
        return self.wrap_nested(path, query)

    def walk__identifier(self, node):
        # Add the current path to field, for example query path(equals|field|val)
        # must yield an es-query in field "path.field"
        field = node.ast
        return self.path + field

    def walk_object(self, node):
        return node

    def walk__string_value(self, node):
        return self.walk(node.ast).lower()

    def walk__quoted_string_value(self, node):
        return "".join([part.replace('\\"', '"') for part in node.ast])

    def is_multi_field(self, field):
        return "*" in field or "," in field

    def single_field(self, query_type, field):
        field = self.walk(field)
        if self.is_multi_field(field):
            raise errors.IncompleteQuery(
                self._q, f"{query_type} queries don't support wildcards in field names"
            )
        return field

    def multi_fields(self, field):
        return field.split(",")

    def regexp(self, field_node, regexp):
        def multi(field):
            return es_dsl.Q(
                "query_string",
                query="/" + regexp.replace("/", "\\/") + "/",
                fields=self.multi_fields(field),
                lenient=True,
            )

        def single(field):
            return es_dsl.Q("regexp", **{field: regexp})

        return self._match_regexp_helper(field_node, multi, single)

    def match(self, field_node, query):
        def multi(field):
            return es_dsl.Q(
                "multi_match", query=query, fields=self.multi_fields(field), lenient=True
            )

        def single(field):
            return es_dsl.Q(
                "match",
                **{field: {"query": query, "operator": "and", "lenient": True}},
            )

        return self._match_regexp_helper(field_node, multi, single)

    def _match_regexp_helper(self, field_node, multi, single):
        if field_node == "*":
            field = field_node
        else:
            field = self.walk(field_node)
        if self.is_multi_field(field):
            query = multi(field)
        else:
            query = single(field)
        return self.wrap_nested(field, query)

    def _exists_missing_range_helper(self, op, node, query_f):
        field = self.single_field(op, node.field)
        q = query_f(field)
        return self.wrap_nested(field, q)


class EsFieldNameCollector(NodeWalker):
    # Return a set of all field names occurring in the given query
    # TODO: support multi-fields too
    def walk_Node(self, node):
        result = set().union(*(self.walk(child) for child in node.children()))
        # TODO maybe a bit too automagic?
        if hasattr(node, "field"):
            result.add(node.field.ast)
        return result

    def walk_object(self, _obj):
        return set()


def _format_result(resource_ids: List[str], response, path: Optional[str] = None):
    def format_entry(entry):
        dict_entry = entry.to_dict()
        version = dict_entry.pop("_entry_version", None)
        last_modified_by = dict_entry.pop("_last_modified_by", None)
        last_modified = dict_entry.pop("_last_modified", None)
        res = {
            "id": entry.meta.id,
            "version": version,
            "last_modified": last_modified,
            "last_modified_by": last_modified_by,
            "resource": next(
                resource for resource in resource_ids if entry.meta.index.startswith(resource)
            ),
            "entry": dict_entry,
        }
        return get_path(path, res) if path else res

    result = {
        "total": response.hits.total.value,
        "hits": [format_entry(entry) for entry in response],
    }
    return result


class EsSearchService:
    @inject
    def __init__(
        self,
        es: elasticsearch.Elasticsearch,
        mapping_repo: EsMappingRepository,
    ):
        self.es: elasticsearch.Elasticsearch = es
        self.mapping_repo = mapping_repo
        self.field_name_collector = EsFieldNameCollector()
        self.parser = KarpQueryV6Parser(semantics=KarpQueryV6ModelBuilderSemantics())

    def query(self, query: QueryRequest):
        logger.info("query called", extra={"request": query})
        return self.search_with_query(query)

    def query_stats(self, resources, q):
        query = QueryRequest(resources=resources, q=q, size=0)
        return self.search_with_query(query)

    def multi_query(self, queries: list[QueryRequest]):
        # ES fails on a multi-search with an empty request list
        if not queries:
            return []

        logger.info(f"multi_query called for {len(queries)} requests")

        ms = es_dsl.MultiSearch(using=self.es)
        for query in queries:
            ms = ms.add(self._build_search(query, query.resources))
        responses = ms.execute()
        return [
            self._build_result(query, response) for query, response in zip(queries, responses)
        ]

    def search_with_query(self, query: QueryRequest):
        logger.info("search_with_query called", extra={"query": query})
        s = self._build_search(query, query.resources)
        response = s.execute()
        return self._build_result(query, response)

    def _build_search(self, query, resources):
        field_names = set()
        es_query = None
        if query.q:
            try:
                model = self.parser.parse(query.q)
                es_query = EsQueryBuilder(resources, self.mapping_repo, query.q).walk(model)
                field_names = self.field_name_collector.walk(model)
            except tatsu_exc.FailedParse as err:
                logger.info("Parse error", extra={"err": err})
                raise errors.IncompleteQuery(
                    failing_query=query.q, error_description=str(err)
                ) from err

        s = es_dsl.Search(using=self.es, index=resources)
        s = self.add_runtime_mappings(s, field_names)
        s = s.extra(track_total_hits=True)  # get accurate hits numbers
        if es_query is not None:
            s = s.query(es_query)

        s = s[query.from_ : query.from_ + query.size]

        if query.lexicon_stats:
            s.aggs.bucket("distribution", "terms", field="_index", size=len(resources))
        if query.size != 0:
            # if no hits are returned, no sorting is needed
            if query.sort:
                s = s.sort(*self.mapping_repo.translate_sort_fields(resources, query.sort))
            else:
                new_s = self.mapping_repo.get_default_sort(resources)
                if new_s:
                    s = s.sort(new_s)

        logger.debug("s = %s", extra={"es_query s": s.to_dict()})
        return s

    def _build_result(self, query, response):
        result = _format_result(query.resources, response, path=query.path)
        if query.lexicon_stats:
            result["distribution"] = {}
            for bucket in response.aggregations.distribution.buckets:
                key = bucket["key"]
                result["distribution"][key.rsplit("_", 1)[0]] = bucket["doc_count"]
        return result

    def add_runtime_mappings(self, s: es_dsl.Search, field_names: set[str]) -> es_dsl.Search:
        # When a query uses a field of the form "f.length", add a
        # runtime_mapping so it gets interpreted as "the length of the field f".
        mappings = {}
        for field in field_names:
            if field.endswith(".length"):
                base_field = field.removesuffix(".length")
                mappings[field] = {
                    "type": "long",
                    "script": {
                        "source": f"emit(doc.containsKey('{base_field}') ? doc['{base_field}'].length : 0)"
                    },
                }

        if mappings:
            s = s.extra(runtime_mappings=mappings)
        return s

    def search_ids(self, resource_id: str, entry_ids: str):
        entries = entry_ids.split(",")
        query = es_dsl.Q("terms", _id=entries)
        logger.debug("query", extra={"query": query})
        s = es_dsl.Search(using=self.es, index=resource_id).query(query)
        logger.debug("s", extra={"es_query s": s.to_dict()})
        response = s.execute()
        return _format_result([resource_id], response)

    def statistics(self, resource_id: str, field: str) -> Iterable:
        s = es_dsl.Search(using=self.es, index=resource_id)
        s = s[:0]

        # if field is analyzed, do aggregation on the "raw" multi-field
        if (
            field in self.mapping_repo.fields[resource_id]
            and self.mapping_repo.fields[resource_id][field].analyzed
        ):
            agg_field = field + ".raw"
        else:
            agg_field = field
        logger.debug(
            "Doing aggregations on resource_id: {resource_id}, on field {field}".format(
                resource_id=resource_id, field=field
            )
        )

        # use an Elasticsearch instance configured to fail at less than 66000 buckets
        # If there are more buckets than that, the ES-lib will raise an exception that we
        # can catch and inform the user.
        max_buckets = 66000

        # if the aggregation field is in a field with type "nested", it needs a special aggregation
        # nested-aggregations counts occurrence of the "sub-documents" and not parent document, this
        # is why the "parent_doc_count" aggregation is needed for its values and sorting
        nest_levels = self.mapping_repo.get_nest_levels(resource_id, field)
        if nest_levels:
            name = "field_values"
            agg = es_dsl.A(
                "terms",
                field=agg_field,
                size=max_buckets,
                order=[{"parent_doc_count": "desc"}],
                # empty reverse_nested means merge on top-level, same result no matter how many levels of nesting there is
                aggs={"parent_doc_count": es_dsl.A("reverse_nested")},
            )
            # add innermost nesting level first
            for level in reversed(nest_levels):
                agg = es_dsl.A("nested", path=level, aggs={name: agg})
                name = level
            s.aggs.bucket(name, agg)
        else:
            s.aggs.bucket("field_values", es_dsl.A("terms", field=agg_field, size=max_buckets))

        try:
            response = s.execute()
        except elasticsearch.BadRequestError as e:
            if e.body["error"]["caused_by"]["type"] == "too_many_buckets_exception":
                raise KarpError("Too many unique values for statistics") from None
            else:
                raise e
        logger.debug("Elasticsearch response", extra={"response": response})
        agg_response = response.aggregations
        if nest_levels:
            # unwrap the doc_count from the "parent_doc_count" aggregation
            for level in nest_levels:
                agg_response = agg_response[level]
            field_values = agg_response["field_values"]
            return [
                {"value": bucket["key"], "count": bucket["parent_doc_count"]["doc_count"]}
                for bucket in field_values.buckets
            ]

        else:
            field_values = agg_response.field_values
            return [
                {"value": bucket["key"], "count": bucket["doc_count"]}
                for bucket in field_values.buckets
            ]
