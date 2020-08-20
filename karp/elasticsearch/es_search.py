import logging
import re
import json

import elasticsearch
import elasticsearch_dsl as es_dsl  # pyre-ignore

from typing import Any, Dict, List, Optional, Set, Tuple, Union

from karp.query_dsl import basic_ast as ast, op, is_a

# from karp import query_dsl
from karp import search
from karp.search.errors import IncompleteQuery, UnsupportedQuery, UnsupportedField
from .index import EsIndex
from .es_observer import OnPublish


logger = logging.getLogger("karp")


class EsQuery(search.Query):
    def __init__(self):
        super().__init__()
        self.query = None
        self.resource_str: Optional[str] = None

    def parse_arguments(self, args, resource_str: str):
        super().parse_arguments(args, resource_str)
        self.resource_str = resource_str
        if not self.ast.is_empty():
            self.query = create_es_query(self.ast.root)

    def _self_name(self) -> str:
        return "EsQuery query={} resource_str={}".format(self.query, self.resource_str)


def get_value(value_node: Union[ast.Node, ast.AnyValue]) -> ast.AnyValue:
    if not isinstance(value_node, ast.Node):
        return value_node
    elif is_a(value_node, op.STRING):
        return value_node.value
    elif is_a(value_node, op.INT):
        return value_node.value
    elif is_a(value_node, op.FLOAT):
        return value_node.value
    else:
        raise IncompleteQuery(
            "Unknown of value (type: {value_node.type}, value: {value_node.value})".format(
                value_node=value_node
            )
        )


def create_es_query(node: ast.Node):
    node.pprint(0)
    if node is None:
        raise TypeError()

    def extract_values(n: ast.Node) -> List[ast.AnyValue]:
        values = []
        if is_a(n, op.ARG_LOGICAL):
            for child in n.children:
                values.append(get_value(child))

        return values

    def extract_values_and_logicals(
        n: ast.Node,
    ) -> Tuple[List[ast.AnyValue], List[ast.Node]]:
        values = []
        logicals = []
        if is_a(n, op.ARG_LOGICAL):
            for child in n.children:
                if is_a(child, op.ARG_LOGICAL):
                    logicals.append(child)
                else:
                    values.append(get_value(child))
        return values, logicals

    def construct_binary_op(field: ast.Node, arg: ast.Node, query_creator):
        q = None
        if is_a(field, op.ARG_LOGICAL):
            if is_a(arg, op.ARG_LOGICAL):
                pass
            else:
                queries = []
                for n in field.children:
                    if is_a(n, op.ARGS):
                        queries.append(query_creator(n, arg))
                    elif is_a(n, op.ARG_LOGICAL):
                        l_queries = []
                        for child in n.children:
                            l_queries.append(query_creator(child, arg))
                        if is_a(n, op.ARG_AND):
                            queries.append(es_dsl.Q("bool", must=l_queries))
                        elif is_a(n, op.ARG_OR):
                            queries.append(es_dsl.Q("bool", should=l_queries))
                        else:
                            queries.append(es_dsl.Q("bool", must_not=l_queries))
                if is_a(arg, op.ARG_AND):
                    q = es_dsl.Q("bool", must=queries)
                elif is_a(arg, op.ARG_OR):
                    q = es_dsl.Q("bool", should=queries)
                else:
                    q = es_dsl.Q("bool", must_not=queries)
                if not arg_values:

                    def prepare_equals_arg(node, v):
                        return v

                    arg = prepare_equals_arg(node, get_value(arg2))
                    queries = [
                        construct_equals_query(field, arg) for field in field_values
                    ]
                    for logical in field_logicals:
                        l_queries = []
                        for field in logical.children:
                            l_queries.append(construct_equals_query(field.value, arg))
                        if is_a(logical, op.ARG_OR):
                            queries.append(es_dsl.Q("bool", should=l_queries))
                        elif is_a(logical, op.ARG_AND):
                            queries.append(es_dsl.Q("bool", must=l_queries))
                        else:
                            queries.append(es_dsl.Q("bool", must_not=l_queries))
                    print(
                        "|create_es_query::EQUALS| queries = {queries}".format(
                            queries=queries
                        )
                    )
                    if is_a(arg1, op.ARG_AND):
                        q = es_dsl.Q("bool", must=queries)
                    elif is_a(arg1, op.ARG_OR):
                        q = es_dsl.Q("bool", should=queries)
                    else:
                        q = es_dsl.Q(
                            "bool",
                            must_not=queries,
                            must=es_dsl.Q("multi_match", query=get_value(arg2)),
                        )
        else:
            if is_a(arg, op.ARG_LOGICAL):
                queries = []
                for n in arg.children:
                    if is_a(n, op.ARGS):
                        queries.append(query_creator(field, n))
                    elif is_a(n, op.ARG_LOGICAL):
                        l_queries = []
                        for child in n.children:
                            l_queries.append(query_creator(field, child))
                        if is_a(n, op.ARG_AND):
                            queries.append(es_dsl.Q("bool", must=l_queries))
                        elif is_a(n, op.ARG_OR):
                            queries.append(es_dsl.Q("bool", should=l_queries))
                        else:
                            queries.append(es_dsl.Q("bool", must_not=l_queries))
                if is_a(arg, op.ARG_AND):
                    q = es_dsl.Q("bool", must=queries)
                elif is_a(arg, op.ARG_OR):
                    q = es_dsl.Q("bool", should=queries)
                else:
                    q = es_dsl.Q("bool", must_not=queries)
            else:
                q = query_creator(field, arg)
        return q

    def construct_equals_query(field: ast.Node, query: ast.Node):
        kwargs = {get_value(field): {"query": get_value(query), "operator": "and"}}
        return es_dsl.Q("match", **kwargs)

    q = None
    if is_a(node, op.LOGICAL):
        # TODO check minimum should match rules in different contexts
        queries = [create_es_query(n) for n in node.children]
        if len(queries) == 2:
            q1 = queries[0]
            q2 = queries[1]
            print("q1 = {}".format(q1.to_dict()))
            print("q2 = {}".format(repr(q2)))
            q1_dict = q1.to_dict()
            q2_dict = q2.to_dict()
            if "range" in q1_dict and "range" in q2_dict:
                for q1_field, q1_value in q1_dict["range"].items():
                    for q2_field, q2_value in q2_dict["range"].items():
                        if q1_field == q2_field:
                            print("q1_field == q2_field")
                            range_args = q1_value
                            range_args.update(q2_value)
                            print("field = {}".format(q1_field))
                            print("range_args = {}".format(range_args))
                            q = es_dsl.Q("range", **{q1_field: range_args})
                            return q
        if is_a(node, op.AND):
            q = es_dsl.Q("bool", must=queries)
        elif is_a(node, op.OR):
            q = es_dsl.Q("bool", should=queries)
        else:
            q = es_dsl.Q("bool", must_not=queries)
    elif is_a(node, op.UNARY_OPS):
        arg = node.children[0]
        arg_values, arg_logicals = extract_values_and_logicals(arg)
        print("arg_values = {}".format(arg_values))
        print("arg_logicals = {}".format(arg_logicals))

        def construct_unary_op(arg: ast.Node, query_creator):
            q = None
            if is_a(arg, op.ARG_LOGICAL):
                queries = []
                for n in arg.children:
                    if is_a(n, op.ARGS):
                        queries.append(query_creator(n))
                    elif is_a(n, op.ARG_LOGICAL):
                        l_queries = []
                        for child in n.children:
                            l_queries.append(query_creator(child))
                        if is_a(n, op.ARG_AND):
                            queries.append(es_dsl.Q("bool", must=l_queries))
                        elif is_a(n, op.ARG_OR):
                            queries.append(es_dsl.Q("bool", should=l_queries))
                        else:
                            queries.append(es_dsl.Q("bool", must_not=l_queries))
                if is_a(arg, op.ARG_AND):
                    q = es_dsl.Q("bool", must=queries)
                elif is_a(arg, op.ARG_OR):
                    q = es_dsl.Q("bool", should=queries)
                else:
                    q = es_dsl.Q("bool", must_not=queries)
            else:
                q = query_creator(arg)
            return q

        def construct_exists_query(node: ast.Node):
            return es_dsl.Q("exists", field=get_value(node))

        if is_a(node, op.FREETEXT):

            def construct_freetext_query(node):
                if is_a(node, op.STRING):
                    return es_dsl.Q("multi_match", query=get_value(node), fuzziness=1)
                else:
                    return es_dsl.Q("multi_match", query=get_value(node))

            if not arg_values:
                q = construct_freetext_query(arg)
            else:
                queries = [construct_freetext_query(n) for n in arg.children]
                if is_a(arg, op.ARG_OR):
                    q = es_dsl.Q("bool", should=queries)
                elif is_a(arg, op.ARG_AND):
                    q = es_dsl.Q("bool", must=queries)
                else:
                    q = es_dsl.Q("bool", must_not=queries)
        elif is_a(node, op.FREERGXP):
            kwargs = {"default_field": "*"}
            if not arg_values:
                kwargs["query"] = "/{}/".format(arg.value)
            else:
                if is_a(arg, op.ARG_OR):
                    operator = " OR "
                else:  # if is_a(arg, op.ARG_AND):
                    operator = " AND "
                kwargs["query"] = operator.join("(/{}/)".format(v) for v in arg_values)
            print("kwargs = {}".format(kwargs))
            q = es_dsl.Q("query_string", **kwargs)
            if is_a(arg, op.ARG_NOT):
                q = es_dsl.Q("bool", must_not=q)
        elif is_a(node, op.EXISTS):
            q = construct_unary_op(node.children[0], construct_exists_query)

        elif is_a(node, op.MISSING):
            if not arg_values:
                q = es_dsl.Q("bool", must_not=es_dsl.Q("exists", field=arg.value))
            else:
                queries = [es_dsl.Q("exists", field=value) for value in arg_values]
                for logical in arg_logicals:
                    l_queries = []
                    for field in logical.children:
                        l_queries.append(construct_exists_query(field))
                    if is_a(logical, op.ARG_AND):
                        queries.append(es_dsl.Q("bool", must=l_queries))
                    elif is_a(logical, op.ARG_OR):
                        queries.append(es_dsl.Q("bool", should=l_queries))
                    else:  # if is_a(logical, op.ARG_NOT):
                        queries.append(es_dsl.Q("bool", must_not=l_queries))

                if is_a(arg, op.ARG_AND):
                    q = es_dsl.Q("bool", must_not=queries)
                elif is_a(arg, op.ARG_OR):
                    q = None
                    for query in queries:
                        q_tmp = es_dsl.Q("bool", must_not=query)
                        if not q:
                            q = q_tmp
                        else:
                            q = q | q_tmp
                else:  # is_a(arg, op.ARG_NOT):
                    q = es_dsl.Q("bool", must=queries)
        else:
            raise UnsupportedQuery("not implemented")
    elif is_a(node, op.BINARY_OPS):
        arg1 = node.children[0]
        arg2 = node.children[1]
        field_values, field_logicals = extract_values_and_logicals(arg1)
        arg_values = extract_values(arg2)

        print("field_values = {field_values}".format(field_values=field_values))
        print("field_logicals = {field_logicals}".format(field_logicals=field_logicals))

        print("arg_values = {}".format(arg_values))
        # TODO this check breaks and and or since they always (?) have ast.ArgNode as parameters
        # if not isinstance(arg1, ast.ArgNode) or not isinstance(arg2, ast.ArgNode):
        # TODO these need to be moved outside of current query, for example:
        # "equals|name||or|Partille|Kumla" could be expressed in two ways
        # es_dsl.Q('terms', name=['Partille', 'Kumla'])
        # or
        # es_dsl.Q('bool', should=[es_dsl.Q('term', name='Partille'), es_dsl.Q('term', name='Kumla')])
        # but "regexp|name||or|Part*|Kum*"
        # can only be expressed as in the longer form above
        # raise UnsupportedQuery()

        if is_a(node, op.EQUALS):

            # q = construct_binary_op(node.children[0], node.children[1], construct_equals_query)
            # if len(field_values) == 1:
            if not field_values and not field_logicals:
                if not arg_values:
                    q = construct_equals_query(arg1, arg2)
                else:
                    queries = [
                        construct_equals_query(get_value(arg1), query)
                        for query in arg_values
                    ]
                    if is_a(arg2, op.ARG_AND):
                        q = es_dsl.Q("bool", must=queries)
                    elif is_a(arg2, op.ARG_OR):
                        q = es_dsl.Q("bool", should=queries)
                    else:
                        q = es_dsl.Q(
                            "bool", must_not=queries
                        )  # , must=es_dsl.Q('multi_match', query=get_value(arg1)))

            else:  # if field_values:
                # if len(arg_values) == 1:
                if not arg_values:

                    def prepare_equals_arg(node, v):
                        return v

                    arg = prepare_equals_arg(node, get_value(arg2))
                    queries = [
                        construct_equals_query(field, arg) for field in field_values
                    ]
                    for logical in field_logicals:
                        l_queries = []
                        for field in logical.children:
                            l_queries.append(construct_equals_query(field.value, arg))
                        if is_a(logical, op.ARG_OR):
                            queries.append(es_dsl.Q("bool", should=l_queries))
                        elif is_a(logical, op.ARG_AND):
                            queries.append(es_dsl.Q("bool", must=l_queries))
                        else:
                            queries.append(es_dsl.Q("bool", must_not=l_queries))
                    print(
                        "|create_es_query::EQUALS| queries = {queries}".format(
                            queries=queries
                        )
                    )
                    if is_a(arg1, op.ARG_AND):
                        q = es_dsl.Q("bool", must=queries)
                    elif is_a(arg1, op.ARG_OR):
                        q = es_dsl.Q("bool", should=queries)
                    else:
                        q = es_dsl.Q(
                            "bool",
                            must_not=queries,
                            must=es_dsl.Q("multi_match", query=get_value(arg2)),
                        )
                else:  # if arg_values:
                    raise UnsupportedQuery("Don't know how to handle ")

        elif is_a(node, op.REGEX_OPS):

            def extract_field_plus_rawfield(field: str):
                if field.endswith(".raw"):
                    yield field
                else:
                    yield field
                    yield field + ".raw"

            def prepare_regex(node, s: str):
                if is_a(node, op.CONTAINS):
                    return ".*" + re.escape(s) + ".*"
                elif is_a(node, op.STARTSWITH):
                    return re.escape(s) + ".*"
                elif is_a(node, op.ENDSWITH):
                    return ".*" + re.escape(s)
                else:
                    return s

            # Construct query
            def construct_regexp_query(field_in: str, regex: str):
                q = None
                for field in extract_field_plus_rawfield(field_in):
                    q_tmp = es_dsl.Q("regexp", **{field: regex})
                    if not q:
                        q = q_tmp
                    else:
                        q = q | q_tmp
                return q

            q = None
            if not field_values and not field_logicals:
                if not arg_values:
                    q = construct_regexp_query(
                        get_value(arg1), prepare_regex(node, get_value(arg2))
                    )
                else:
                    queries = []
                    for regex in arg_values:
                        q_tmp = construct_regexp_query(
                            get_value(arg1), prepare_regex(node, regex)
                        )
                        print("q_tmp = {q_tmp}".format(q_tmp=q_tmp))

                        queries.append(q_tmp)

                    if is_a(arg2, op.ARG_OR):
                        q = es_dsl.Q("bool", should=queries)
                    elif is_a(arg2, op.ARG_AND):
                        q = es_dsl.Q("bool", must=queries)
                    else:
                        q = es_dsl.Q(
                            "bool", must_not=queries
                        )  # , must=es_dsl.Q('query_string', **kwargs))
            else:  # if field_values:
                if not arg_values:
                    regex = prepare_regex(node, get_value(arg2))
                    queries = []
                    for field in field_values:
                        q_tmp = construct_regexp_query(field, regex)
                        print("q_tmp = {q_tmp}".format(q_tmp=q_tmp))

                        queries.append(q_tmp)
                    for logical in field_logicals:
                        l_queries = []
                        for field in logical.children:
                            l_queries.append(construct_regexp_query(field.value, regex))
                        if is_a(logical, op.ARG_OR):
                            queries.append(es_dsl.Q("bool", should=l_queries))
                        elif is_a(logical, op.ARG_AND):
                            queries.append(es_dsl.Q("bool", must=l_queries))
                        else:
                            queries.append(es_dsl.Q("bool", must_not=l_queries))

                    print(
                        "|create_es_query::REGEX| queries = {queries}".format(
                            queries=queries
                        )
                    )
                    if is_a(arg1, op.ARG_OR):
                        q = es_dsl.Q("bool", should=queries)
                    elif is_a(arg1, op.ARG_AND):
                        q = es_dsl.Q("bool", must=queries)
                    else:
                        kwargs = {"default_field": "*"}
                        kwargs["query"] = "/{}/".format(regex)

                        print("regex NOT kwargs = {}".format(kwargs))

                        q = es_dsl.Q(
                            "bool",
                            must_not=queries,
                            must=es_dsl.Q("query_string", **kwargs),
                        )
                else:
                    raise UnsupportedQuery("Complex regex not implemented")

        elif is_a(node, op.RANGE_OPS):
            if arg_values:
                raise UnsupportedQuery(
                    "Not allowed to use logical operators in 2nd argument for RANGE operators."
                )

            def prepare_range_args(node, arg22):
                range_args = {}
                if is_a(node, op.LT):
                    range_args["lt"] = arg22
                elif is_a(node, op.LTE):
                    range_args["lte"] = arg22
                elif is_a(node, op.GT):
                    range_args["gt"] = arg22
                elif is_a(node, op.GTE):
                    range_args["gte"] = arg22
                return range_args

            range_args = prepare_range_args(node, get_value(arg2))

            def construct_range_query(field: str, range_args: Dict):
                return es_dsl.Q("range", **{field: range_args})

            q = None
            if not field_values:
                q = construct_range_query(get_value(arg1), range_args)
            else:
                queries = [construct_range_query(f, range_args) for f in field_values]
                for logical in field_logicals:
                    l_queries = []
                    for field in logical.children:
                        l_queries.append(construct_range_query(field.value, range_args))
                    if is_a(logical, op.ARG_OR):
                        queries.append(es_dsl.Q("bool", should=l_queries))
                    elif is_a(logical, op.ARG_AND):
                        queries.append(es_dsl.Q("bool", must=l_queries))
                    else:
                        queries.append(es_dsl.Q("bool", must_not=l_queries))
                print(
                    "|create_es_query::RANGE| queries = {queries}".format(
                        queries=queries
                    )
                )
                if is_a(arg1, op.ARG_AND):
                    q = es_dsl.Q("bool", must=queries)
                elif is_a(arg1, op.ARG_OR):
                    q = es_dsl.Q("bool", should=queries)
                else:
                    q = es_dsl.Q("bool", must_not=queries)
    # elif isinstance(node, ast.TernaryOp):
    #     op = node.value
    #     arg1 = node.children[0]
    #     arg2 = node.children[1]
    #     arg3 = node.children[2]
    #     if op == query_dsl.Operators.RANGE:
    #         raise UnsupportedQuery('don\'t now what to do yet')
    #     else:
    #         raise UnsupportedQuery('what operators?')
    else:
        raise UnsupportedQuery("Unknown query op '{node}'".format(node=node))

    return q


class EsSearch(search.SearchInterface):
    class UpdateFieldsOnPublish(OnPublish):
        def __init__(self, outer):
            self.outer = outer

        def update(self, *, alias_name: str, index_name: str, **kwargs):
            self.outer.on_publish_resource(alias_name, index_name)

    def __init__(self, es: elasticsearch.Elasticsearch, es_index: EsIndex):
        self.es: elasticsearch.Elasticsearch = es
        analyzed_fields, sortable_fields = self._init_field_mapping()
        self.analyzed_fields: Dict[str, List[str]] = analyzed_fields
        self.sortable_fields: Dict[str, Dict[str, List[str]]] = sortable_fields
        self.update_fields_on_publish = EsSearch.UpdateFieldsOnPublish(self)
        es_index.register_publish_observer(self.update_fields_on_publish)

    @staticmethod
    def get_analyzed_fields_from_mapping(
        properties: Dict[str, Dict[str, Dict[str, Any]]]
    ) -> List[str]:
        analyzed_fields = []

        for prop_name, prop_values in properties.items():
            if "properties" in prop_values:
                res = EsSearch.get_analyzed_fields_from_mapping(
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
                field_mapping[alias] = EsSearch.get_analyzed_fields_from_mapping(
                    mapping[index]["mappings"]["entry"]["properties"]
                )
                sortable_fields[alias] = EsSearch.create_sortable_map_from_mapping(
                    mapping[index]["mappings"]["entry"]["properties"]
                )
        return field_mapping, sortable_fields

    def _get_index_mappings(
        self, index: Optional[str] = None
    ) -> Dict[str, Dict[str, Dict[str, Dict[str, Dict]]]]:
        if index is not None:
            kwargs = {"index": index}
        else:
            kwargs = {}

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

    def search_with_query(self, query: EsQuery):
        logger.info("search_with_query called with query={}".format(query))
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

    def search_ids(self, args, resource_id: str, entry_ids: str):
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
            ] = EsSearch.get_analyzed_fields_from_mapping(
                mapping[index_name]["mappings"]["entry"]["properties"]
            )
            self.sortable_fields[
                alias_name
            ] = EsSearch.create_sortable_map_from_mapping(
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
