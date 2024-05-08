import dataclasses  # noqa: I001
import typing
from typing import Dict, Iterable, Optional

from injector import Injector, Module, provider, singleton

from karp.search.infrastructure.es import EsIndex
from karp.foundation.timings import utc_now
from karp.search.domain.index_entry import IndexEntry


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

    def create_index(self, resource_id: str, config: Dict):  # noqa: ANN201
        self.indices[resource_id] = InMemoryIndex.Index(config=config, created_at=utc_now())

    def publish_index(self, alias_name: str, index_name: str = None):  # noqa: ANN201
        self.indices[alias_name].published = True

    def add_entries(  # noqa: ANN201
        self, resource_id: str, entries: Iterable[IndexEntry]
    ):
        for entry in entries:
            self.indices[resource_id].entries[entry.id] = entry

    def delete_entry(  # noqa: ANN201
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
        del self.indices[resource_id].entries[entry_id]

    def _save(self, _notused):  # noqa: ANN202
        pass

    def _by_id(self, id) -> None:  # noqa: A002
        return None


class InMemorySearchInfrastructure(Module):
    @provider
    @singleton
    def index(self) -> EsIndex:
        return InMemoryIndex()
