import dataclasses
from typing import Dict, Iterable, List, Optional

import injector

from karp.foundation.commands import CommandBus
from karp.foundation.events import EventBus
from karp.foundation.time import utc_now
from karp.lex.application.repositories import entries
from karp.lex.domain.entities import entry
from karp.search.application.repositories import IndexUnitOfWork, Index, IndexEntry
from karp.tests.foundation.adapters import InMemoryUnitOfWork


@dataclasses.dataclass
class SearchUnitTestContext:
    container: injector.Injector
    command_bus: CommandBus
    event_bus: EventBus


class InMemoryIndex(Index):
    @dataclasses.dataclass
    class Index:
        config: Dict
        created_at: float
        entries: Dict[str, IndexEntry] = dataclasses.field(default_factory=dict)
        created: bool = True
        published: bool = False

    def __init__(self) -> None:
        super().__init__()
        self.indicies: dict[str, InMemoryIndex.Index] = {}
        self.seen = []

    def create_index(self, resource_id: str, config: Dict):
        self.indicies[resource_id] = InMemoryIndex.Index(
            config=config, created_at=utc_now()
        )

    def publish_index(self, alias_name: str, index_name: str = None):
        self.indicies[alias_name].published = True

    def add_entries(self, resource_id: str, entries: Iterable[IndexEntry]):
        for entry in entries:
            self.indicies[resource_id].entries[entry.id] = entry

    def delete_entry(
        self,
        resource_id: str,
        *,
        entry_id: Optional[str] = None,
        # entry: typing.Optional[model.Entry]
    ):
        if entry_id is None:
            return
        if not isinstance(entry_id, str):
            entry_id = str(entry_id)
        del self.indicies[resource_id].entries[entry_id]

    #    def search_ids(self, resource_id: str, entry_ids: str):
    #        return {}
    #
    #    def query(self, request: search_service.QueryRequest):
    #        return {}
    #
    #    def query_split(self, request: search_service.QueryRequest):
    #        return {}
    #
    #    def statistics(self, resource_id: str, field: str):
    #        return {}
    def num_entities(self) -> int:
        return sum(len(entries) for entries in self.indicies.values())


class InMemoryIndexUnitOfWork(InMemoryUnitOfWork, IndexUnitOfWork):
    def __init__(self):
        # super().__init__()
        self._index = InMemoryIndex()

    @property
    def repo(self) -> InMemoryIndex:
        return self._index


class InMemorySearchInfrastructure(injector.Module):
    @injector.provider
    @injector.singleton
    def index_uow(self) -> IndexUnitOfWork:
        return InMemoryIndexUnitOfWork()
