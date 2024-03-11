import typing

import elasticsearch_dsl as es_dsl

from karp.search.domain import Query, QueryRequest


class EsQuery(Query):
    query: typing.Optional[es_dsl.query.Query] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def from_query_request(cls, request: QueryRequest):
        query = cls(fields=[], resources=request.resource_ids, sort=[])
        query.from_ = request.from_
        query.size = request.size
        query.lexicon_stats = request.lexicon_stats
        query.q = request.q or ""
        query.sort = request.sort
        return query

    class Config:
        arbitrary_types_allowed = True
