import abc

from karp.lex.domain import entities as lex_entities
from karp.search.domain import search_service


class EntryTransformer(abc.ABC):
    @abc.abstractmethod
    def transform(self, resource_id: str, entry: lex_entities.Entry) -> search_service.IndexEntry:
        pass
