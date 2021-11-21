import abc

from karp.lex.domain import entities as lex_entities
from karp.search.application.repositories import IndexEntry


class EntryTransformer(abc.ABC):
    @abc.abstractmethod
    def transform(
        self,
        resource_id: str,
        entry: lex_entities.Entry,
    ) -> IndexEntry:
        pass
