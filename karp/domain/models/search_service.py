from typing import Optional, Callable, TypeVar, List, Dict, Tuple

from karp.domain.models.query import Query
from karp.domain.models.entry import Entry


class SearchService:
    def create_index(self, resource_id: str, config: Dict) -> str:
        raise NotImplementedError()

    def publish_index(self, alias_name: str, index_name: str):
        raise NotImplementedError()

    def add_entries(
        self, resource_id: str, entries: List[Entry]
    ):
        raise NotImplementedError()

    def delete_entry(self, resource_id: str, entry_id: str):
        raise NotImplementedError()

    def create_empty_object(self):
        raise NotImplementedError()

    def assign_field(self, _index_entry, field_name: str, part):
        raise NotImplementedError()

    def create_empty_list(self):
        raise NotImplementedError()

    def add_to_list_field(self, elems: List, elem):
        raise NotImplementedError()

    def build_query(self, args, resource_str: str) -> Query:
        query = Query()
        query.parse_arguments(args, resource_str)
        return query

    def search_with_query(self, query: Query):
        raise NotImplementedError()

    def search_ids(self, args, resource_id: str, entry_ids: str):
        raise NotImplementedError()

    def statistics(self, resource_id: str, field: str):
        raise NotImplementedError()
