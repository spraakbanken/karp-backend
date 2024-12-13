import logging
from typing import Iterable, List, Optional

import elasticsearch
import elasticsearch.helpers
import elasticsearch_dsl as es_dsl
from injector import inject
from tatsu import exceptions as tatsu_exc
from tatsu.walkers import NodeWalker

from karp.foundation.json import get_path
from karp.main.errors import KarpError
from karp.search.domain import QueryRequest, errors
from karp.search.domain.query_dsl.karp_query_model import KarpQueryModelBuilderSemantics, ModelBase
from karp.search.domain.query_dsl.karp_query_parser import KarpQueryParser
from karp.search.infrastructure.es import mapping_repo as es_mapping_repo
from karp.search.infrastructure.es.mapping_repo import EsMappingRepository, Field

logger = logging.getLogger(__name__)


class EsQueryBuilder(NodeWalker):
    def __init__(self, resources, mapping_repo, q=None):
        super().__init__()
        self._q = q
        self.path = ""
        self.resources = resources
        self.mapping_repo = mapping_repo

    def walk__equals(self, node):
        (field_path, field) = self.walk(node.field)
        if field.type != "text":
            return self.wrap_nested(field_path, es_dsl.Q("match", **{field_path: {"query": self.walk(node.arg)}}))
        return self.match_text(field_path, self.walk(node.arg), phrase=True)

    def walk__freetext(self, node):
        value = self.walk(node.arg)
        query = self.match_text(self.path + "*", value)

        nested_fields = set()
        for resource_id in self.resources:
            nested_fields.update(self.mapping_repo.get_nested_fields(resource_id, self.path))

        for nested_field in nested_fields:
            # adding the field name for nested fields will trigger match to generate es_dsl.Q("nested", ...) where needed
            query = query | self.match_text(nested_field + ".*", value)
        return query

    def walk__regexp(self, node):
        return self.regexp(node.field, self.walk(node.arg))

    def walk__contains(self, node):
        return self.regexp(node.field, f".*{self.walk(node.arg)}.*")

    def walk__startswith(self, node):
        return self.regexp(node.field, f"{self.walk(node.arg)}.*")

    def walk__endswith(self, node):
        return self.regexp(node.field, f".*{self.walk(node.arg)}")

    def walk__exists(self, node):
        field_path, _ = self.walk(node.field)
        return self.wrap_nested(field_path, es_dsl.Q("exists", field=field_path))

    def walk__missing(self, node):
        q = self.walk__exists(node)
        return es_dsl.Q("bool", must_not=q)

    def walk_range(self, node):
        field_path, _ = self.walk(node.field)
        return self.wrap_nested(
            field_path,
            es_dsl.Q("range", **{field_path: {self.walk(node.op): self.walk(node.arg)}}),
        )

    walk__gt = walk_range
    walk__gte = walk_range
    walk__lt = walk_range
    walk__lte = walk_range

    def walk__not(self, node):
        must_nots = [self.walk(expr) for expr in node.ast]
        return es_dsl.Q("bool", must_not=must_nots)

    def walk__or(self, node):
        if not node.ast:
            return es_dsl.Q("match_none")

        result = self.walk(node.ast[0])
        for n in node.ast[1:]:
            result = result | self.walk(n)

        return result

    def walk__and(self, node):
        if not node.ast:
            return es_dsl.Q("match_all")

        result = self.walk(node.ast[0])
        for n in node.ast[1:]:
            result = result & self.walk(n)

        return result

    def walk__sub_query(self, node):
        (field_path, _) = self.walk(node.field)
        self.path = field_path + "."
        query = self.walk(node.exp)
        self.path = ""
        return self.wrap_nested(field_path, query)

    def wrap_nested(self, field_path, query):
        """
        field_path is a string representing the field to be search in, which may be a path separated by "."
        query is the ES (DSL) query to be wrapped
        """
        # if field_path and self.path is the same, no extra nesting needed
        if field_path + "." == self.path:
            return query

        try:
            is_nested = self.mapping_repo.is_nested(self.resources, field_path)
        except ValueError:
            raise errors.IncompleteQuery(
                self._q,
                f"Resources: {self.resources} have different settings for field: {field_path}",
            ) from None

        if is_nested:
            query = es_dsl.Q("nested", path=field_path, query=query)

        path, *last_elem = field_path.rsplit(".", 1)
        if not last_elem:
            return query

        # check if there are most nested fields in the remaining path
        return self.wrap_nested(path, query)

    def walk__identifier(self, node):
        field_name = node.ast
        if "*" in field_name:
            field = Field(path=[field_name], type="any")
        else:
            # Add the current path to field, for example query path(equals|field|val)
            # must yield an es-query in field "path.field"
            field = self.mapping_repo.get_field(self.resources, self.path + field_name)
        return field.name, field

    def walk_object(self, node):
        return node

    def walk__string_value(self, node):
        return self.walk(node.ast).lower()

    def walk__quoted_string_value(self, node):
        return "".join([part.replace('\\"', '"') for part in node.ast])

    def is_multi_field(self, field):
        return "*" in field or "," in field

    def multi_fields(self, field):
        return field.split(",")

    def regexp(self, field_node, regexp):
        (field_path, field) = self.walk(field_node)
        if field.type not in ["text", "keyword"]:
            raise ValueError("Query type only allowed on text and keyword")
        q = es_dsl.Q(
            "query_string",
            query="/" + regexp.replace("/", "\\/") + "/",
            fields=[field_path],
            lenient=True,
        )
        return self.wrap_nested(field_path, q)

    def match_text(self, field_path, query, phrase=False):
        if self.is_multi_field(field_path) or not phrase:
            query = es_dsl.Q(
                "multi_match",
                query=query,
                fields=self.multi_fields(field_path),
                lenient=True,
                type="phrase",
            )
        else:
            query = es_dsl.Q("match_phrase", **{field_path: query})
        return self.wrap_nested(field_path, query)


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


def _format_result(response, path: Optional[str] = None, highlight: bool = False):
    def format_entry(entry):
        dict_entry = entry.to_dict()

        res = {
            "id": entry.meta.id,
            "entry": dict_entry,
        }
        if highlight and hasattr(entry.meta, "highlight"):
            res["highlight"] = entry.meta.highlight.to_dict()
        for mapped_name, field in es_mapping_repo.internal_fields.items():
            res[mapped_name] = dict_entry.pop(field.name, None)

        return get_path(path, res) if path else res

    result = {
        "total": response.hits.total.value,
        "hits": [format_entry(entry) for entry in response],
    }
    return result


def _build_result(query, response):
    result = _format_result(response, path=query.path, highlight=query.highlight)
    if query.lexicon_stats:
        result["distribution"] = {}
        for bucket in response.aggregations.distribution.buckets:
            key = bucket["key"]
            result["distribution"][key.rsplit("_", 1)[0]] = bucket["doc_count"]
    return result


def _add_runtime_mappings(s: es_dsl.Search, field_names: set[str]) -> es_dsl.Search:
    # When a query uses a field of the form "f.length", add a
    # runtime_mapping so it gets interpreted as "the length of the field f".
    mappings = {}
    for field in field_names:
        if field.endswith(".length"):
            base_field = field.removesuffix(".length")
            mappings[field] = {
                "type": "long",
                "script": {"source": f"emit(doc.containsKey('{base_field}') ? doc['{base_field}'].length : 0)"},
            }

    if mappings:
        s = s.extra(runtime_mappings=mappings)
    return s


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
        self.parser = KarpQueryParser(semantics=KarpQueryModelBuilderSemantics())

    def query(self, query: QueryRequest):
        logger.info("query called", extra={"request": query})
        return self._search_with_query(query)

    def query_stats(self, resources, q):
        query = QueryRequest(resources=resources, q=q, size=0)
        return self._search_with_query(query)

    def multi_query(self, queries: list[QueryRequest]):
        # ES fails on a multi-search with an empty request list
        if not queries:
            return []

        logger.info(f"multi_query called for {len(queries)} requests")

        # Workaround: MultiSearch.add takes linear time in the size of
        # the query
        class WorkaroundMultiSearch(es_dsl.MultiSearch):
            def add(self, search):
                self._searches.append(search)
                return self

        ms = WorkaroundMultiSearch(using=self.es)
        for query in queries:
            ms = ms.add(self._build_search(query, query.resources))
        responses = ms.execute()
        return [_build_result(query, response) for query, response in zip(queries, responses)]

    def _search_with_query(self, query: QueryRequest):
        logger.info("search_with_query called", extra={"query": query})
        s = self._build_search(query, query.resources)
        response = s.execute()
        return _build_result(query, response)

    def _build_search(self, query, resources):
        field_names = set()
        es_query = None
        if query.q:
            try:
                if isinstance(query.q, ModelBase):
                    model = query.q
                else:
                    model = self.parser.parse(query.q)
                es_query = EsQueryBuilder(resources, self.mapping_repo, query.q).walk(model)
                field_names = self.field_name_collector.walk(model)
            except tatsu_exc.FailedParse as err:
                logger.info("Parse error", extra={"err": err})
                raise errors.IncompleteQuery(failing_query=query.q, error_description=str(err)) from err

        s = es_dsl.Search(using=self.es, index=resources)
        s = _add_runtime_mappings(s, field_names)
        s = s.extra(track_total_hits=True)  # get accurate hits numbers
        if es_query is not None:
            s = s.query(es_query)

        s = s[query.from_ : query.from_ + query.size]

        if query.lexicon_stats:
            s.aggs.bucket("distribution", "terms", field="_index", size=len(resources))
        if query.highlight:
            # only highlight the fields that are used in query
            for field in field_names:
                # add the actual field
                s = s.highlight(field)
                # also highlight any fields in "subobject" (will not match anything if field is a leaf)
                s = s.highlight(field + ".*")
            if not field_names:
                # i.e. freetext
                s = s.highlight("*")
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

    def search_ids(self, resource_id: str, entry_ids: List[str]):
        query = es_dsl.Q("terms", _id=entry_ids)
        logger.debug("query", extra={"query": query})
        s = es_dsl.Search(using=self.es, index=resource_id).query(query)
        logger.debug("s", extra={"es_query s": s.to_dict()})
        response = s.execute()
        return _format_result(response)

    def statistics(self, resource_id: str, field: str) -> Iterable:
        s = es_dsl.Search(using=self.es, index=resource_id)
        s = s[:0]

        # if field is analyzed, do aggregation on the "raw" multi-field
        if field in self.mapping_repo.fields[resource_id] and self.mapping_repo.fields[resource_id][field].analyzed:
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
            return [{"value": bucket["key"], "count": bucket["doc_count"]} for bucket in field_values.buckets]
