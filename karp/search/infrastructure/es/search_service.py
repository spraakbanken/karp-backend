import logging
import re
from collections import defaultdict
from typing import Iterable

import elasticsearch
import elasticsearch.helpers
import elasticsearch_dsl as es_dsl
from injector import inject
from tatsu import exceptions as tatsu_exc
from tatsu.walkers import NodeWalker

from karp.foundation.json import get_path
from karp.main.errors import KarpError, QueryParserError
from karp.search.domain import QueryRequest
from karp.search.domain.highlight_param import HighlightParam
from karp.search.domain.query_dsl.karp_query_model import KarpQueryModelBuilderSemantics, ModelBase
from karp.search.domain.query_dsl.karp_query_parser import KarpQueryParser
from karp.search.infrastructure.es import mapping_repo as es_mapping_repo
from karp.search.infrastructure.es.mapping_repo import EsMappingRepository, Field

logger = logging.getLogger(__name__)


class EsQueryBuilder(NodeWalker):
    def __init__(self, resources, mapping_repo, highlight=False):
        super().__init__()
        self.path = [""]
        self.length_mappings = set()
        self.resources = resources
        self.mapping_repo = mapping_repo
        self.highlight = highlight

    def walk__freetext(self, node):
        value = self.walk(node.arg)

        # using * to include all fields would include unanalyzed .raw fields, so we must list fields explicitly
        tree = self.mapping_repo.get_fields_as_tree(self.resources, self.path)

        def recurse(tree: dict, path: str):
            queries = []
            for key, obj in tree.items():
                full_field = path + "." + key if path else key
                if not obj["children"]:
                    # a leaf, add concrete query
                    if obj["def"].type == "text":
                        query = es_dsl.Q("match_phrase", **{full_field: value})
                    else:
                        query = es_dsl.Q("match", **{full_field: {"query": value, "lenient": True}})
                else:
                    # has children, recurse with new path
                    self.path.append(full_field + ".")
                    query = recurse(obj["children"], full_field)
                    self.path.pop()

                queries.append(self.wrap_nested(full_field, query))

            if len(queries) > 1:
                return es_dsl.Q("bool", should=queries)
            return queries[0]

        # generate query recursively beginning with an empty path
        return recurse(tree, "")

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

    def walk__field_query(self, node):
        """
        handles exists or misssing
        """
        field_path, _ = self.walk(node.field)
        exists_q = self.wrap_nested(field_path, es_dsl.Q("exists", field=field_path))
        if node.op == "missing":
            return es_dsl.Q("bool", must_not=exists_q)
        return exists_q

    def binary_query_expression(self, node):
        """
        coordinating value output with field config, keyword fields should not lowercase arguments
        """
        field_path, field = self.walk(node.field)
        arg = self.walk(node.arg)
        if isinstance(arg, str) and field.type != "keyword":
            arg = arg.lower()
        return self.binary_query(node.op, field_path, field, arg)

    def walk__text_arg_expression(self, node):
        """
        Added node type TextArgExpression to enable faster scripting
        """
        return self.binary_query_expression(node)

    def walk__any_arg_expression(self, node):
        """
        Added node type AnyArgExpression to enable faster scripting
        """
        return self.binary_query_expression(node)

    def walk__sub_query(self, node):
        (field_path, _) = self.walk(node.field)
        self.path.append(field_path + ".")
        query = self.walk(node.exp)
        self.path.pop()
        return self.wrap_nested(field_path, query)

    def wrap_nested(self, field_path, query):
        """
        field_path is a string representing the field to be search in, which may be a path separated by "."
        query is the ES (DSL) query to be wrapped
        """
        # if field_path and self.path is the same, no extra nesting needed
        if field_path + "." == self.path[-1]:
            return query

        if self.mapping_repo.is_nested(self.resources, field_path):
            inner_hits = {}
            if self.highlight:
                inner_hits = {"inner_hits": {"_source": False, "highlight": {"fields": {}}}}
                non_nested_children = self.mapping_repo.get_non_nested_children(self.resources, field_path)
                for field in non_nested_children:
                    inner_hits["inner_hits"]["highlight"]["fields"][field] = {}
            query = es_dsl.Q("nested", path=field_path, query=query, **inner_hits)

        path, *last_elem = field_path.rsplit(".", 1)
        if not last_elem:
            return query

        # check if there are most nested fields in the remaining path
        return self.wrap_nested(path, query)

    def walk__identifier(self, node):
        field_path: str = node.ast
        is_length = field_path.endswith(".length")
        if "*" in field_path:
            field_obj = Field(path=[field_path], type="any")
            return field_obj.name, field_obj
        else:
            # Add the current path to field, for example query path(equals|field|val)
            # must yield an es-query in field "path.field"
            field_obj = self.mapping_repo.get_field(self.resources, self.path[-1] + field_path.removesuffix(".length"))
            # if the field query has ".length" appended, and the field is text, we must query raw
            if is_length:
                if field_obj.type == "text":
                    mapping = field_obj.name + ".raw.length"
                else:
                    mapping = field_obj.name + ".length"
                self.length_mappings.add(mapping)
            else:
                mapping = field_obj.name
            return mapping, field_obj

    def walk_object(self, node):
        return node

    def walk__string_value(self, node):
        return self.walk(node.ast)

    def walk__quoted_string_value(self, node):
        return "".join([part.replace('\\"', '"') for part in node.ast])

    def is_multi_field(self, field):
        return "*" in field or "," in field

    def multi_fields(self, field):
        return field.split(",")

    def binary_query(self, op, field_path, field, arg):
        if op == "equals":
            if field.type != "text":
                return self.wrap_nested(field_path, es_dsl.Q("match", **{field_path: {"query": arg}}))
            return self.match_text(field_path, self.walk(arg), phrase=True)
        elif op == "regexp":
            return self.regexp(field_path, field, arg)
        elif op == "contains":
            return self.regexp(field_path, field, f".*{arg}.*")
        elif op == "startswith":
            return self.regexp(field_path, field, f"{arg}.*")
        elif op == "endswith":
            return self.regexp(field_path, field, f".*{arg}")
        elif op in ["gt", "gte", "lt", "lte"]:
            return self.wrap_nested(field_path, es_dsl.Q("range", **{field_path: {op: arg}}))

    def regexp(self, field_path, field, regexp):
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
    """
    Return a set of all field names occurring in the given query
    # TODO: support multi-fields too
    """

    def walk_Node(self, node):
        result = set()
        if isinstance(node.ast, list):
            result = result.union(*(self.walk(child) for child in node.ast))
        elif hasattr(node, "field"):
            result.add(node.field.ast)
        return result

    def walk__sub_query(self, node):
        fields = self.walk(node.exp)
        identifier = node.field.ast
        return {identifier + "." + field for field in fields}

    def walk_object(self, _obj):
        return set()


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


def remove_indices_from_path(path: str) -> str:
    return re.sub(r"\[.*?\]", "", path)


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
        logger.debug("query called", extra={"request": query})
        return self._search_with_query(query)

    def query_stats(self, resources, q):
        query = QueryRequest(resources=resources, q=q, size=0)
        return self._search_with_query(query)

    def multi_query(self, queries: list[QueryRequest]):
        # ES fails on a multi-search with an empty request list
        if not queries:
            return []

        logger.debug(f"multi_query called for {len(queries)} requests")

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
        return [self._build_result(query, response) for query, response in zip(queries, responses)]

    def _search_with_query(self, query: QueryRequest):
        logger.debug("search_with_query called", extra={"query": query})
        s = self._build_search(query, query.resources)
        response = s.execute()
        return self._build_result(query, response)

    def _build_search(self, query, resources: list[str]):
        field_names = set()
        es_query = None
        builder = None
        if query.q:
            try:
                if isinstance(query.q, ModelBase):
                    model = query.q
                else:
                    model = self.parser.parse(query.q)
                builder = EsQueryBuilder(
                    resources, self.mapping_repo, highlight=query.highlight != HighlightParam.false
                )
                es_query = builder.walk(model)
                field_names = self.field_name_collector.walk(model)
            except tatsu_exc.FailedParse as err:
                raise QueryParserError(failing_query=str(query.q), error_description=str(err)) from err

        s = es_dsl.Search(using=self.es, index=resources)
        if builder:
            s = _add_runtime_mappings(s, builder.length_mappings)
        s = s.extra(track_total_hits=True)  # get accurate hits numbers
        if es_query is not None:
            s = s.query(es_query)

        if query.size:
            s = s[query.from_ : query.from_ + query.size]
        else:
            # Elasticsearch defaults to only 10 results if size is unspecified
            # TODO: how can we return all results? By default it only allows
            # from + size <= 10000
            s = s[query.from_ : 10000]

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

    def _format_result(self, response, path: str | None = None, highlight: HighlightParam = HighlightParam.false):
        def format_nested_highlight(result_tree) -> dict[str, list[str]]:
            """
            recursively find the innermost inner_hits which contain highlights and list index values
            """
            final_highlights = {}
            for key, inner_hit_outer in result_tree.meta.inner_hits.items():
                for inner_hit in inner_hit_outer.hits:
                    # just move through to the tree until the innermost inner_hit is found
                    if hasattr(inner_hit.meta, "inner_hits"):
                        final_highlights.update(format_nested_highlight(inner_hit))

                    if hasattr(inner_hit.meta, "nested"):

                        def get_path(path, obj):
                            """
                            the nested field of the inner_hit is a recursive structure
                            this function returns the actual path with indices
                            and also the path without indices, which is needed to match
                            the correct highlight to the correct path with indices
                            """
                            if path:
                                path = path + "."
                            path = path + obj.field + f"[{obj.offset}]"
                            if hasattr(obj, "_nested"):
                                return get_path(path, obj._nested)
                            return path

                        path = get_path("", inner_hit.meta.nested)

                        for key, hit_highlights in getattr(inner_hit.meta, "highlight", {}).items():
                            # this finds the final fields needed to complete the path to the matching field
                            extra_fields = key.split(remove_indices_from_path(path))[1]
                            final_highlights[path + extra_fields] = hit_highlights

            return final_highlights

        def format_entry(entry):
            dict_entry = entry.to_dict()

            res = {
                "resource": self.mapping_repo.reverse_aliases[entry.meta.index],
                "id": entry.meta.id,
                "entry": dict_entry,
            }
            if highlight != HighlightParam.false and hasattr(entry.meta, "highlight"):
                res["highlight"] = entry.meta.highlight.to_dict()

                if hasattr(entry.meta, "inner_hits"):
                    # group the inner_hits by the path without indices
                    inner_hits_highlights = defaultdict(dict)
                    for highlight_path, highlight_item in format_nested_highlight(entry).items():
                        # for now, remove the "global" highlighting and replace with the one from inner_hits
                        path_wo_indices = remove_indices_from_path(highlight_path)
                        inner_hits_highlights[path_wo_indices][highlight_path] = highlight_item

                    # remove duplicates from the outer highlighting
                    for path_wo_indices in inner_hits_highlights.keys():
                        res["highlight"].pop(path_wo_indices, None)

                    # for compatibility reasons, if HighlightParam.true, use older format without indices
                    # this can be removed when frontend has updated to use the new format with indices.
                    if highlight == HighlightParam.true:
                        for path_wo_indices, val in inner_hits_highlights.items():
                            # flatten for path_wo_indices
                            res["highlight"][path_wo_indices] = [
                                inner_highlight
                                for inner_highlights in val.values()
                                for inner_highlight in inner_highlights
                            ]
                    else:
                        for val in inner_hits_highlights.values():
                            res["highlight"].update(val)

            for mapped_name, field in es_mapping_repo.internal_fields.items():
                res[mapped_name] = dict_entry.pop(field.name, None)

            return get_path(path, res) if path else res

        result = {
            "total": response.hits.total.value,
            "hits": [format_entry(entry) for entry in response],
        }
        return result

    def _build_result(self, query, response):
        result = self._format_result(response, path=query.path, highlight=query.highlight)
        if query.lexicon_stats:
            result["distribution"] = {}
            for bucket in response.aggregations.distribution.buckets:
                key = bucket["key"]
                result["distribution"][key.rsplit("_", 1)[0]] = bucket["doc_count"]
        return result

    def search_ids(self, resource_id: str, entry_ids: list[str]):
        query = es_dsl.Q("terms", _id=entry_ids)
        logger.debug("query", extra={"query": query})
        s = es_dsl.Search(using=self.es, index=resource_id).query(query)
        logger.debug("s", extra={"es_query s": s.to_dict()})
        response = s.execute()
        return self._format_result(response)

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
