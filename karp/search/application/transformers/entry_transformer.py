import abc

from karp import lex
from karp.search.application.repositories import IndexEntry


class EntryTransformer(abc.ABC):
    @abc.abstractmethod
    def transform(
        self,
        resource_id: str,
        src_entry: lex.EntryDto,
    ) -> IndexEntry:
        pass
