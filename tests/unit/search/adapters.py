import dataclasses
from typing import Dict, Iterable, Optional

from injector import Injector, Module, provider, singleton

from karp.foundation.timings import utc_now
from karp.search.domain.index_entry import IndexEntry
from karp.search.infrastructure.es import EsIndex


@dataclasses.dataclass
class SearchUnitTestContext:
    injector: Injector


class InMemoryIndex(EsIndex):
    @dataclasses.dataclass
    class Index:
        config: Dict
        created_at: float
        entries: Dict[str, IndexEntry] = dataclasses.field(default_factory=dict)
        created: bool = True
        published: bool = False

    def __init__(self) -> None:
        super().__init__()
        self.indices: dict[str, InMemoryIndex.Index] = {}

    def create_index(self, resource_id: str, config, create_alias=True):
        self.indices[resource_id] = InMemoryIndex.Index(config=config, created_at=utc_now())

    def publish_index(self, alias_name: str, index_name: str | None = None):  # noqa: ANN201
        self.indices[alias_name].published = True

    def add_entries(  # noqa: ANN201
        self, resource_id: str, entries: Iterable[IndexEntry]
    ):
        for entry in entries:
            self.indices[resource_id].entries[entry.id] = entry

    def delete_entry(
        self,
        resource_id: str,
        *,
        entry_id: Optional[str] = None,
    ):
        if entry_id is None:
            return
        if not isinstance(entry_id, str):
            entry_id = str(entry_id)
        del self.indices[resource_id].entries[entry_id]


class InMemorySearchInfrastructure(Module):
    @provider
    @singleton
    def index(self) -> EsIndex:
        return InMemoryIndex()
