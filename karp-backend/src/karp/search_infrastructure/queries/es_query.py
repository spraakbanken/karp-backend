import typing  # noqa: D100
from typing import Union  # noqa: F401

import elasticsearch_dsl as es_dsl
from karp.search.application.queries import QueryRequest
from karp.search.domain.errors import IncompleteQuery, UnsupportedQuery  # noqa: F401
from karp.search.domain.query import Query
from karp.search.domain.query_dsl import basic_ast as ast  # noqa: F401
from karp.search.domain.query_dsl import is_a, op  # noqa: F401


class EsQuery(Query):  # noqa: D101
    query: typing.Optional[es_dsl.query.Query] = None
    resource_str: typing.Optional[str] = None

    def __init__(self, **kwargs):  # noqa: ANN003, ANN204, D107
        super().__init__(**kwargs)
        # self.query = None
        # self.resource_str: Optional[str] = None

    def parse_arguments(self, args, resource_str: str):  # noqa: ANN201, D102
        super().parse_arguments(args, resource_str)
        self.resource_str = resource_str
        # if not self.ast.is_empty():
        #     self.query = create_es_query(self.ast.root)

    def _self_name(self) -> str:
        return f"EsQuery query={self.query} resource_str={self.resource_str}"

    @classmethod
    def from_query_request(cls, request: QueryRequest):  # noqa: ANN206, D102
        query = cls(fields=[], resources=request.resource_ids, sort=[])
        query.from_ = request.from_
        query.size = request.size
        query.lexicon_stats = request.lexicon_stats
        query.q = request.q or ""
        query.sort = request.sort
        return query

    class Config:  # noqa: D106
        arbitrary_types_allowed = True
