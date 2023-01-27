import abc
import logging
import typing
from typing import Callable, Dict, List, Optional, Tuple, TypeVar

import pydantic

from karp.search.domain.query import Query

logger = logging.getLogger(__name__)


class EntryDto(pydantic.BaseModel):
    id: str
    version: int
    last_modified: float
    last_modified_by: str
    resource: str
    entry: typing.Dict


class QueryResponseBase(pydantic.BaseModel):
    hits: list[EntryDto]
    total: int
    distribution: typing.Optional[dict[str, int]]


class QueryResponse(QueryResponseBase):
    pass


class QuerySplitResponse(QueryResponseBase):
    distribution: dict[str, int]


class StatisticsDto(pydantic.BaseModel):
    value: str
    count: int


class QueryRequest(pydantic.BaseModel):  # pylint: disable=no-member
    resource_ids: typing.List[str]
    q: typing.Optional[str] = None
    from_: int = 0
    size: int = 25
    lexicon_stats: bool = True
    sort: List[str] = pydantic.Field(default_factory=list)

    @pydantic.validator("resource_ids", pre=True)
    @classmethod
    def split_str(cls, v):
        if isinstance(v, str):
            return v.split(",")
        return v


class SearchService(abc.ABC):

    # def build_query(self, args, resource_str: str) -> Query:
    #     query = Query()
    #     query.parse_arguments(args, resource_str)
    #     return query

    # def build_query_parsed(self, args, resource_str: str) -> Query:
    #     query = Query()
    #     query.parse_arguments(args, resource_str)
    #     return query

    # def search_with_query(self, query: Query):
    #     raise NotImplementedError()

    @abc.abstractmethod
    def search_ids(self, resource_id: str, entry_ids: str):
        raise NotImplementedError()

    @abc.abstractmethod
    def query(self, request: QueryRequest):
        raise NotImplementedError()

    @abc.abstractmethod
    def query_split(self, request: QueryRequest):
        raise NotImplementedError()

    @abc.abstractmethod
    def statistics(
        self, resource_id: str, field: str
    ) -> typing.Iterable[StatisticsDto]:
        raise NotImplementedError()
