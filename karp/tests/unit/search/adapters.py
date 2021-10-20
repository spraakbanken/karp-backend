import dataclasses
from typing import Dict, List, Optional

import injector

from karp.foundation.commands import CommandBus
from karp.foundation.events import EventBus
from karp.search.application.repositories import SearchServiceUnitOfWork
from karp.search.domain import search_service
from karp.tests.foundation.adapters import FakeUnitOfWork


@dataclasses.dataclass
class SearchUnitTestContext:
    container: injector.Injector
    command_bus: CommandBus
    event_bus: EventBus


class FakeSearchService(search_service.SearchService):
    @dataclasses.dataclass
    class Index:
        config: Dict
        entries: Dict[str, search_service.IndexEntry] = dataclasses.field(
            default_factory=dict
        )
        created: bool = True
        published: bool = False

    def __init__(self) -> None:
        super().__init__()
        self.indicies = {}
        self.seen = []

    def create_index(self, resource_id: str, config: Dict):
        self.indicies[resource_id] = FakeSearchService.Index(config=config)

    def publish_index(self, alias_name: str, index_name: str = None):
        self.indicies[alias_name].published = True

    def add_entries(self, resource_id: str, entries: List[search_service.IndexEntry]):
        for entry in entries:
            self.indicies[resource_id].entries[entry.id] = entry

    def delete_entry(
        self,
        resource_id: str,
        *,
        entry_id: Optional[str],
        # entry: typing.Optional[model.Entry]
    ):
        del self.indicies[resource_id].entries[entry_id]

    def search_ids(self, resource_id: str, entry_ids: str):
        return {}

    def query(self, request: search_service.QueryRequest):
        return {}

    def query_split(self, request: search_service.QueryRequest):
        return {}

    def statistics(self, resource_id: str, field: str):
        return {}


class FakeSearchServiceUnitOfWork(
    FakeUnitOfWork, SearchServiceUnitOfWork
):
    def __init__(self):
        # super().__init__()
        self._index = FakeSearchService()

    @property
    def repo(self) -> search_service.SearchService:
        return self._index


class FakeSearchInfrastructure(injector.Module):
    @injector.provider
    @injector.singleton
    def search_service_uow(self) -> SearchServiceUnitOfWork:
        return FakeSearchServiceUnitOfWork()
