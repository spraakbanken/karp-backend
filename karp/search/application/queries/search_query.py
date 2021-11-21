import abc
import typing

from karp.search.domain import search_service


class SearchQuery(abc.ABC):

    @abc.abstractmethod
    def search_ids(self, resource_id: str, entry_ids: str):
        pass

    @abc.abstractmethod
    def query(self, req: search_service.QueryRequest):
        pass

    @abc.abstractmethod
    def query_split(self, req: search_service.QueryRequest):
        pass

    @abc.abstractmethod
    def statistics(self, resource_id: str, field: str):
        pass
