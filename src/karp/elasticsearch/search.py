import re
import elasticsearch_dsl as es_dsl  # pyre-ignore

from karp.query_dsl import basic_ast as ast
from karp import search
from karp import query_dsl


class EsQuery(search.Query):
    def __init__(self):
        super().__init__()
        self.query = None
        self.resource_str = None

    def parse_arguments(self, args, resource_str):
        super().parse_arguments(args, resource_str)
        self.resource_str = resource_str
        if not self.ast.is_empty():
            self.query = create_es_query(self.ast.root)

    def _self_name(self) -> str:
        return 'EsQuery query={} resource_str={}'.format(self.query,
                                                         self.resource_str)


def get_value(value_node):
    if isinstance(value_node, ast.StringNode):
        return value_node.value
    elif isinstance(value_node, ast.IntNode):
        return value_node.value
    elif isinstance(value_node, ast.FloatNode):
        return value_node.value
    else:
        raise NotImplementedError()


def create_es_query(node):
    if node is None:
        raise TypeError()

    q = None
    if isinstance(node, ast.UnaryOp):
        op = node.value
        value = get_value(node.child0)
        if op == query_dsl.Operators.FREETEXT:
            if isinstance(node.child0, ast.StringNode):
                q = es_dsl.Q('multi_match', query=value, fuzziness=1)
            else:
                q = es_dsl.Q('multi_match', query=value)
        elif op == query_dsl.Operators.FREERGXP:
            q = es_dsl.Q('regexp', freetext=value)
        elif op == query_dsl.Operators.EXISTS:
            q = es_dsl.Q('exists', field=value)
        elif op == query_dsl.Operators.MISSING:
            q = es_dsl.Q('bool', must_not=es_dsl.Q('exists', field=value))
        else:
            raise RuntimeError('not implemented')
    elif isinstance(node, ast.BinaryOp):
        op = node.value
        arg1 = node.child0
        arg2 = node.child1

        if not isinstance(arg1, ast.ArgNode) or not isinstance(arg2, ast.ArgNode):
            # TODO these need to be moved outside of current query, for example:
            # "equals|name||or|Partille|Kumla" could be expressed in two ways
            # es_dsl.Q('terms', name=['Partille', 'Kumla'])
            # or
            # es_dsl.Q('bool', should=[es_dsl.Q('term', name='Partille'), es_dsl.Q('term', name='Kumla')])
            # but "regexp|name||or|Part*|Kum*"
            # can only be expressed as in the longer form above
            raise RuntimeError()

        if op in [query_dsl.Operators.AND, query_dsl.Operators.OR]:
            # TODO check minimum should match rules in different contexts
            q1 = create_es_query(arg1)
            q2 = create_es_query(arg2)
            if op == query_dsl.Operators.AND:
                q = es_dsl.Q('bool', must=[q1, q2])
            else:
                q = es_dsl.Q('bool', should=[q1, q2])
        elif op in [query_dsl.Operators.EQUALS, query_dsl.Operators.REGEXP, query_dsl.Operators.CONTAINS,
                    query_dsl.Operators.STARTSWITH, query_dsl.Operators.ENDSWITH]:
            arg11 = get_value(arg1)
            arg22 = get_value(arg2)
            if op == query_dsl.Operators.EQUALS:
                query_type = 'term'
            elif op == query_dsl.Operators.REGEXP:
                query_type = 'regexp'
            elif op == query_dsl.Operators.CONTAINS:
                query_type = 'regexp'
                arg22 = '.*' + re.escape(arg22) + '.*'
            elif op == query_dsl.Operators.STARTSWITH:
                query_type = 'regexp'
                arg22 = re.escape(arg22) + '.*'
            else:  # query_dsl.Operators.ENDSWITH
                query_type = 'regexp'
                arg22 = '.*' + re.escape(arg22)
            q = es_dsl.Q(query_type, **{arg11: arg22})
        elif op in [query_dsl.Operators.LT, query_dsl.Operators.LTE, query_dsl.Operators.GT, query_dsl.Operators.GTE]:
            range_args = {}
            arg11 = get_value(arg1)
            arg22 = get_value(arg2)
            if op == query_dsl.Operators.LT:
                range_args['lt'] = arg22
            elif op == query_dsl.Operators.LTE:
                range_args['lte'] = arg22
            elif op == query_dsl.Operators.GT:
                range_args['gt'] = arg22
            elif op == query_dsl.Operators.GTE:
                range_args['gte'] = arg22
            q = es_dsl.Q('range', **{arg11: range_args})
    elif isinstance(node, ast.TernaryOp):
        op = node.value
        arg1 = node.child0
        arg2 = node.child1
        arg3 = node.child2
        if op == query_dsl.Operators.RANGE:
            raise RuntimeError('don\'t now what to do yet')
        else:
            raise RuntimeError('what operators?')
    else:
        raise ValueError('Unknown query op %s' % node)

    return q


class EsSearch(search.SearchInterface):

    def __init__(self, es):
        self.es = es

    def build_query(self, args, resource_str: str) -> EsQuery:
        query = EsQuery()
        query.parse_arguments(args, resource_str)
        return query

    def search_with_query(self, query: EsQuery):
        print('search_with_query called with query={}'.format(query))
        if query.split_results:
            ms = es_dsl.MultiSearch(using=self.es)

            for resource in query.resources:
                s = es_dsl.Search(index=resource)
                if query.query is not None:
                    s = s.query(query.query)
                ms = ms.add(s)

            responses = ms.execute()
            result = {}
            for i, response in enumerate(responses):
                result[query.resources[i]] = [part_result.to_dict() for part_result in response]

            return result
        else:
            s = es_dsl.Search(using=self.es, index=query.resource_str)
            print('s = {}'.format(s))
            if query.query is not None:
                s = s.query(query.query)
            response = s.execute()

            return [{'id': result.meta.id, 'version': -1, 'entry': result.to_dict()} for result in response]
