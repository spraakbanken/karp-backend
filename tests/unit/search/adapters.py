import dataclasses  # noqa: I001
import typing
from typing import Dict, Iterable, Optional

import injector

from karp.command_bus import CommandBus
from karp.foundation import repository
from karp.foundation.events import EventBus
from karp.timings import utc_now
from karp.search.application.repositories import IndexUnitOfWork, IndexEntry
from tests.foundation.adapters import InMemoryUnitOfWork


@dataclasses.dataclass
class SearchUnitTestContext:
    container: injector.Injector
    command_bus: CommandBus
    event_bus: EventBus


class InMemoryIndex(repository.Repository):
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

    def create_index(self, resource_id: str, config: Dict):  # noqa: ANN201
        self.indicies[resource_id] = InMemoryIndex.Index(config=config, created_at=utc_now())

    def publish_index(self, alias_name: str, index_name: str = None):  # noqa: ANN201
        self.indicies[alias_name].published = True

    def add_entries(  # noqa: ANN201
        self, resource_id: str, entries: Iterable[IndexEntry]
    ):
        for entry in entries:
            self.indicies[resource_id].entries[entry.id] = entry

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
        del self.indicies[resource_id].entries[entry_id]

    def create_empty_object(self) -> IndexEntry:  # noqa: D102
        return IndexEntry(id="", entry={})

    def assign_field(  # noqa: ANN201, D102
        self, _index_entry: IndexEntry, field_name: str, part
    ):
        if isinstance(part, IndexEntry):
            part = part.entry
        _index_entry.entry[field_name] = part

    def add_to_list_field(self, elems: typing.List, elem):  # noqa: ANN201, D102
        if isinstance(elem, IndexEntry):
            elem = elem.entry
        elems.append(elem)

    def _save(self, _notused):  # noqa: ANN202
        pass

    def _by_id(self, id) -> None:  # noqa: A002
        return None


class InMemoryIndexUnitOfWork(InMemoryUnitOfWork, IndexUnitOfWork):
    def __init__(self, event_bus: EventBus):  # noqa: ANN204
        IndexUnitOfWork.__init__(self, event_bus=event_bus)  # type:ignore [arg-type]
        self._index = InMemoryIndex()

    @property
    def repo(self) -> InMemoryIndex:
        return self._index


class InMemorySearchInfrastructure(injector.Module):
    @injector.provider
    @injector.singleton
    def index_uow(self, event_bus: EventBus) -> IndexUnitOfWork:
        return InMemoryIndexUnitOfWork(event_bus=event_bus)
