import typing

import pydantic

from karp.search.domain import QueryRequest


class EsQuery(pydantic.BaseModel):
    resources: list[str] = []
    sort: list[str] = []
    from_: int = pydantic.Field(0, alias="from")
    size: int = 25
    lexicon_stats: bool = True
    path: typing.Optional[list[str]] = None
    q: typing.Optional[str] = None
    sort_dict: typing.Optional[dict[str, list[str]]] = pydantic.Field(default_factory=dict)

    @classmethod
    def from_query_request(cls, request: QueryRequest):
        query = cls()
        query.resources = request.resource_ids
        query.from_ = request.from_
        query.size = request.size
        query.lexicon_stats = request.lexicon_stats
        query.q = request.q or ""
        query.sort = request.sort or []
        query.path = request.path
        return query

    class Config:
        arbitrary_types_allowed = True
