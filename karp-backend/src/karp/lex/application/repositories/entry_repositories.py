import abc  # noqa: D100, I001
from typing import Dict, Optional, Protocol, Tuple

import injector

from karp.foundation import repository, unit_of_work, events
from karp.lex_core.value_objects import UniqueId
from karp.lex.domain import errors
from .entries import EntryUnitOfWork


class EntryUowRepositoryUnitOfWork(unit_of_work.UnitOfWork):
    def __init__(  # noqa: D107, ANN204
        self,
        *,
        event_bus: events.EventBus,
    ):
        unit_of_work.UnitOfWork.__init__(self, event_bus)

    @abc.abstractmethod
    def create(
        self,
        id: UniqueId,  # noqa: A002
        name: str,
        config: dict,
        connection_str: Optional[str],
        user: str,
        message: str,
        timestamp: float,
    ) -> Tuple[EntryUnitOfWork, list[events.Event]]:
        raise NotImplementedError
