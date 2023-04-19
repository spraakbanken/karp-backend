import abc

from karp import lex
from karp.search.application.repositories import IndexEntry


class EntryTransformer(abc.ABC):  # noqa: D101
    @abc.abstractmethod
    def transform(  # noqa: D102
        self,
        resource_id: str,
        src_entry: lex.EntryDto,
    ) -> IndexEntry:
        pass
