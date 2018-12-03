from typing import List
from abc import ABCMeta, abstractmethod





class ParseError(BaseException):
    msg: str

    def __init__(self, msg: str) -> None:
        self.msg = msg


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


class QueryOperator(metaclass=ABCMeta):
    ARITY = None
    NAME = None

    @classmethod
    def name(cls) -> str:
        return cls.NAME

    @classmethod
    def arity(cls) -> int:
        return cls.ARITY

    def add_args(self, args: List[str]) -> None:
        if len(args) < self.arity():
            raise ParseError("Too few arguments to '{}'".format(self.name()))
        if len(args) > self.arity():
            raise ParseError("Too many arguments to '{}'".format(self.name()))
        self.add_args_impl(args)

    @abstractmethod
    def add_args_impl(self, args: List[str]) -> None:
        pass


class FreeText(QueryOperator):
    NAME = 'freetext'
    ARITY = 1
    arg = None

    def add_args_impl(self, args: List[str]) -> None:
        self.arg = args[0]


class QueryOperatorManager:
    OPERATORS = [FreeText]

    def get(self, name: str) -> QueryOperator:
        for operator in self.OPERATORS:
            if name == operator.name():
                return operator()
        # Unknown QueryOperator
        raise RuntimeError


queryOpMgr = QueryOperatorManager()


class Query(object):
    query: QueryOperator = None

    def __init__(self, q) -> None:
        if isinstance(q, QueryOperator):
            self.query = q
        else:
            raise RuntimeError


def get_query_operator(name: str) -> QueryOperator:
    return queryOpMgr.get(name)


def parse_query(q: str) -> Query:
    # logical_ops = q.split('|||')
    # logical_exprs = q.split('||')
    def parse_query_expr(qe: str):
        query_expr = qe.split('|')
        if len(query_expr) < 1:
            raise ParseError('Empty QueryExpression')

        operator = get_query_operator(query_expr[0])
        op_args = query_expr[1:]
        operator.add_args(op_args)
        return operator

    query_op = parse_query_expr(q)
    return Query(query_op)
