import abc  # noqa: D100, I001
from typing import Dict, Optional, Protocol, Tuple

import injector

from karp.foundation import repository, unit_of_work, events
from karp.lex_core.value_objects import UniqueId
from karp.lex.domain import errors
from .entries import EntryUnitOfWork


class EntryUnitOfWorkCreator(Protocol):  # noqa: D101
    def __call__(  # noqa: D102
        self,
        id: UniqueId,  # noqa: A002
        name: str,
        config: dict,
        connection_str: Optional[str],
        user: str,
        message: str,
        timestamp: float,
    ) -> Tuple[EntryUnitOfWork, list[events.Event]]:
        ...


class EntryUowRepositoryUnitOfWork(unit_of_work.UnitOfWork):
    def __init__(  # noqa: D107, ANN204
        self,
        *,
        event_bus: events.EventBus,
        entry_uow_factory: EntryUnitOfWorkCreator,
    ):
        unit_of_work.UnitOfWork.__init__(self, event_bus)
        self._entry_uow_factory = entry_uow_factory

    @property
    def factory(self) -> EntryUnitOfWorkCreator:  # noqa: D102
        return self._entry_uow_factory
