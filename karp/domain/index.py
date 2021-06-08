import abc
import typing
from karp.domain.models.resource import Resource
from typing import Optional, Callable, TypeVar, List, Dict, Tuple
import logging

import attr
import pydantic

from karp.domain import errors, model
from karp.domain.errors import ConfigurationError

from karp.domain.models.query import Query
from karp.domain.models.entry import Entry


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
    to: int = 25
    lexicon_stats: bool = True

    @pydantic.validator("resource_ids", pre=True)
    def split_str(cls, v):
        if isinstance(v, str):
            return v.split(",")
        return v


class Index(abc.ABC):
    _registry = {}

    def __init_subclass__(
        cls, index_type: str, is_default: bool = False, **kwargs
    ) -> None:
        super().__init_subclass__(**kwargs)
        if index_type is None:
            raise RuntimeError("Unallowed index_type: index_type = None")
        if index_type in cls._registry:
            raise RuntimeError(
                f"An Index with type '{index_type}' already exists: {cls._registry[index_type]!r}"
            )
        index_type = index_type.lower()
        cls._registry[index_type] = cls
        if is_default or None not in cls._registry:
            logger.info("Setting default Index type to '%s'", index_type)
            cls._registry[None] = index_type

    @classmethod
    def create(cls, index_type: Optional[str]):
        if index_type is None:
            index_type = cls._registry[None]
        else:
            index_type = index_type.lower()

        try:
            index_cls = cls._registry[index_type]
        except KeyError:
            raise ConfigurationError(f"Can't create a Index of type '{index_type}'")
        return index_cls()

    @abc.abstractmethod
    def create_index(self, resource_id: str, config: Dict):
        pass

    @abc.abstractmethod
    def publish_index(self, alias_name: str, index_name: str = None):
        pass

    @abc.abstractmethod
    def add_entries(self, resource_id: str, entries: List[IndexEntry]):
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

    def statistics(self, resource_id: str, field: str):
        raise NotImplementedError()
