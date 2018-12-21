from typing import List
from abc import ABCMeta, abstractmethod

from .basic_ast import *





class ParseError(BaseException):
    msg: str

    def __init__(self, msg: str) -> None:
        self.msg = msg


LOGICAL_OPERATORS = {
    'and': binary_logical_operator('AND'),
    'or': binary_logical_operator('OR'),
    'not': logical_operator('NOT', 1, 2),
}

QUERY_OPERATORS = {
    'freetext': query_operator('FREETEXT', 1, 2),
    'regexp': query_operator('REGEXP', 1, 3),
    'exists': query_operator('EXISTS', 1, 2),
    'missing': query_operator('MISSING', 1, 2),
    'equals': query_operator('EQUALS', 2, 3),
    'contains': query_operator('CONTAINS', 2, 3),
    'startswith': query_operator('STARTSWITH', 2, 3),
    'endswith': query_operator('ENDSWITH', 2, 3),
    'lt': query_operator('LT', 2, 3),
    'lte': query_operator('LTE', 2, 3),
    'gt': query_operator('GT', 2, 3),
    'gte': query_operator('GTE', 2, 3),
    'range': query_operator('RANGE', 3, 4),
}

OPERATORS = {**LOGICAL_OPERATORS, **QUERY_OPERATORS}


def create_ast_node(s: str) -> AstNode:
    node_creator = OPERATORS.get(s)
    if not node_creator:
        try:
            int_value = int(s)
            return IntNode(int_value)
        except ValueError:
            pass

        try:
            float_value = float(s)
            return FloatNode(float_value)
        except ValueError:
            pass

        return StringNode(s)

    return node_creator()


def _sub_expr(node, s):
    exprs = s.split('|')

    _node = create_ast_node(exprs[0])

    if not isinstance(_node, ArgNode):
        for expr in exprs[1:]:
            _node.add_child(create_ast_node(expr))

    node.add_child(_node)


def _expr(node, s):
    exprs = s.split('||')

    if len(exprs) == 1:
        return _sub_expr(node, s)

    nodes = []
    for expr in exprs:
        if not expr:
            continue
        tmp_node = AstNode()
        rest = _sub_expr(tmp_node, expr)


        nodes.append(tmp_node.children[0])

    _node = nodes.pop()
    _store = []
    while nodes:
        _tmp = nodes.pop()
        if isinstance(_tmp, BinLogOpNode):
            left = nodes.pop()
            right = _node
            _node = _tmp
            _node.left = left
            _node.right = right
        elif isinstance(_tmp, LogOpNode):
            if isinstance(_node, BinLogOpNode):
                child = _node.left
                _tmp.add_child(child)
                _node.left = _tmp
            else:
                child = _node
                _node = _tmp
                _node.add_child(child)
        elif isinstance(_tmp, OpNode):
            # child = _node
            # _node = _tmp
            # _node.add_child(child)
            _tmp.add_child(_node)
            _node = _tmp
            if _node.num_children() < _node.max_arity:
                if _store:
                    _node.add_child(_store.pop())
        elif isinstance(_tmp, ArgNode):
            if isinstance(_node, ArgNode):
                _store.append(_node)
                _node = _tmp

    node.add_child(_node)


def parse(s: str) -> Ast:
    # print('parsing "{}"'.format(s))
    tmp_node = AstNode()
    rest = _expr(tmp_node, s)
    if rest:
        print('rest: ', rest)
    ast = Ast(tmp_node.children[0])
    return ast

# class ParseResult:
#     error: ParseError
#     ok: Query
#
#     def __init__(self, ok=None, error=None) -> None:
#         if ok and not error:
#             self.ok = ok
#             return
#         if error and not ok:
#             self.error = error
#             return
#         raise RuntimeError


# class QueryOperator(metaclass=ABCMeta):
#     ARITY = None
#     NAME = None
#
#     @classmethod
#     def name(cls) -> str:
#         return cls.NAME
#
#     @classmethod
#     def arity(cls) -> int:
#         return cls.ARITY
#
#     def add_args(self, args: List[str]) -> None:
#         if len(args) < self.arity():
#             raise ParseError("Too few arguments to '{}'".format(self.name()))
#         if len(args) > self.arity():
#             raise ParseError("Too many arguments to '{}'".format(self.name()))
#         self.add_args_impl(args)
#
#     @abstractmethod
#     def add_args_impl(self, args: List[str]) -> None:
#         pass
#
#
# class FreeText(QueryOperator):
#     NAME = 'freetext'
#     ARITY = 1
#     arg = None
#
#     def add_args_impl(self, args: List[str]) -> None:
#         self.arg = args[0]
#
#
# class QueryOperatorManager:
#     OPERATORS = [FreeText]
#
#     def get(self, name: str) -> QueryOperator:
#         for operator in self.OPERATORS:
#             if name == operator.name():
#                 return operator()
#         # Unknown QueryOperator
#         raise RuntimeError
#
#
# queryOpMgr = QueryOperatorManager()
#
#
# class Query(object):
#     query: QueryOperator = None
#
#     def __init__(self, q) -> None:
#         if isinstance(q, QueryOperator):
#             self.query = q
#         else:
#             raise RuntimeError
#
#
# def get_query_operator(name: str) -> QueryOperator:
#     return queryOpMgr.get(name)
#
#
# def parse_query(q: str) -> Query:
#     # logical_ops = q.split('|||')
#     # logical_exprs = q.split('||')
#     def parse_query_expr(qe: str):
#         query_expr = qe.split('|')
#         if len(query_expr) < 1:
#             raise ParseError('Empty QueryExpression')
#
#         operator = get_query_operator(query_expr[0])
#         op_args = query_expr[1:]
#         operator.add_args(op_args)
#         return operator
#
#     query_op = parse_query_expr(q)
#     return Query(query_op)
