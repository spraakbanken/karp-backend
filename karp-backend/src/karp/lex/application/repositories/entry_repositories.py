import abc  # noqa: D100, I001
from typing import Dict, Optional, Protocol, Tuple

import injector

from karp.foundation import repository, unit_of_work, events
from karp.lex_core.value_objects import UniqueId
from karp.lex.domain import errors
from .entries import EntryUnitOfWork


class EntryRepositoryUnitOfWorkFactory:  # noqa: D101
    @abc.abstractmethod
    def create(  # noqa: D102
        self,
        repository_type: str,
        id: UniqueId,  # noqa: A002
        name: str,
        config: dict,
        connection_str: Optional[str],
        user: str,
        message: str,
        timestamp: float,
    ) -> Tuple[EntryUnitOfWork, list[events.Event]]:
        pass


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


class InjectorEntryUnitOfWorkRepoFactory(  # noqa: D101
    EntryRepositoryUnitOfWorkFactory
):
    def __init__(self, container: injector.Injector) -> None:  # noqa: D107
        self._container = container

    def create(  # noqa: D102
        self,
        repository_type: str,
        id: UniqueId,  # noqa: A002
        name: str,
        config: dict,
        connection_str: Optional[str],
        user: str,
        message: str,
        timestamp: float,
    ) -> Tuple[EntryUnitOfWork, list[events.Event]]:
        uow_factory_cls = self._container.get(Dict[str, EntryUnitOfWorkCreator])[
            repository_type
        ]

        uow_factory: EntryUnitOfWorkCreator = self._container.create_object(
            uow_factory_cls  # type: ignore[arg-type]
        )
        return uow_factory(
            id=id,
            name=name,
            config=config,
            connection_str=connection_str,
            user=user,
            message=message,
            timestamp=timestamp,
        )


class EntryUowRepository(repository.Repository[EntryUnitOfWork]):  # noqa: D101
    EntityNotFound = errors.EntryRepoNotFound
    pass


class EntryUowRepositoryUnitOfWork(  # noqa: D101
    unit_of_work.UnitOfWork[EntryUowRepository]
):
    def __init__(  # noqa: D107, ANN204
        self,
        *,
        event_bus: events.EventBus,
        entry_uow_factory: EntryRepositoryUnitOfWorkFactory,
    ):
        unit_of_work.UnitOfWork.__init__(self, event_bus)
        self._entry_uow_factory = entry_uow_factory

    @property
    def factory(self) -> EntryRepositoryUnitOfWorkFactory:  # noqa: D102
        return self._entry_uow_factory
