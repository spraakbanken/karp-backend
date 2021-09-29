import abc
import logging
import typing
from typing import Callable, Dict, List, Optional, Tuple, TypeVar

import attr
import pydantic

from karp.domain import errors, model
from karp.domain.errors import ConfigurationError
from karp.domain.models.entry import Entry
from karp.domain.models.query import Query
from karp.domain.models.resource import Resource

logger = logging.getLogger("karp")


@attr.s(auto_attribs=True)
class IndexEntry:
    id: str = attr.Factory(str)
    entry: Dict = attr.Factory(dict)

    def __bool__(self) -> bool:
        return bool(self.entry)


class QueryRequest(pydantic.BaseModel):  # pylint: disable=no-member
    resource_ids: typing.List[str]
    q: typing.Optional[str] = None
    from_: int = 0
    size: int = 25
    lexicon_stats: bool = True
    sort: List[str] = pydantic.Field(default_factory=list)

    @pydantic.validator("resource_ids", pre=True)
    def split_str(cls, v):
        if isinstance(v, str):
            return v.split(",")
        return v


class Index(abc.ABC):

    @abc.abstractmethod
    def create_index(self, resource_id: str, config: Dict):
        pass

    @abc.abstractmethod
    def publish_index(self, resource_id: str):
        pass

    @abc.abstractmethod
    def add_entries(self, resource_id: str, entries: typing.Iterable[IndexEntry]):
        pass

    @abc.abstractmethod
    def delete_entry(
        self,
        resource_id: str,
        *,
        entry_id: Optional[str] = None,
        # entry: Optional[Entry] = None,
    ):
        pass

    def create_empty_object(self) -> IndexEntry:
        return IndexEntry()

    def assign_field(self, _index_entry: IndexEntry, field_name: str, part):
        if isinstance(part, IndexEntry):
            part = part.entry
        _index_entry.entry[field_name] = part

    def create_empty_list(self) -> List:
        return []

    def add_to_list_field(self, elems: List, elem):
        elems.append(elem)

    def build_query(self, args, resource_str: str) -> Query:
        query = Query()
        query.parse_arguments(args, resource_str)
        return query

    def build_query_parsed(self, args, resource_str: str) -> Query:
        query = Query()
        query.parse_arguments(args, resource_str)
        return query

    def search_with_query(self, query: Query):
        raise NotImplementedError()

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
    def statistics(self, resource_id: str, field: str):
        raise NotImplementedError()
