import abc  # noqa: D100
from typing import Iterable

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

    @abc.abstractmethod
    def update_references(  # noqa: D102
        self,
        resource_id: str,
        # resource_repo: ResourceRepository,
        # indexer: SearchService,
        # resource: entities.Resource,
        entry_ids: Iterable[str],
    ) -> None:
        pass
