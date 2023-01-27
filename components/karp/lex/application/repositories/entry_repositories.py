import abc
from typing import Dict, Optional, Protocol

import injector

from karp.foundation import repository, unit_of_work, events
from karp.foundation.value_objects import UniqueId
from karp.lex.domain import errors
from .entries import EntryUnitOfWork


class EntryRepositoryUnitOfWorkFactory:
    @abc.abstractmethod
    def create(
        self,
        repository_type: str,
        entity_id: UniqueId,
        name: str,
        config: dict,
        connection_str: Optional[str],
        user: str,
        message: str,
        timestamp: float,
    ) -> EntryUnitOfWork:
        pass


class EntryUnitOfWorkCreator(Protocol):
    def __call__(
        self,
        entity_id: UniqueId,
        name: str,
        config: dict,
        connection_str: Optional[str],
        user: str,
        message: str,
        timestamp: float,
    ) -> EntryUnitOfWork:
        ...


class InjectorEntryUnitOfWorkRepoFactory(EntryRepositoryUnitOfWorkFactory):
    def __init__(self, container: injector.Injector) -> None:
        self._container = container

    def create(
        self,
        repository_type: str,
        entity_id: UniqueId,
        name: str,
        config: dict,
        connection_str: Optional[str],
        user: str,
        message: str,
        timestamp: float,
    ) -> EntryUnitOfWork:
        uow_factory_cls = self._container.get(Dict[str, EntryUnitOfWorkCreator])[
            repository_type
        ]

        uow_factory: EntryUnitOfWorkCreator = self._container.create_object(
            uow_factory_cls
        )
        return uow_factory(
            entity_id=entity_id,
            name=name,
            config=config,
            connection_str=connection_str,
            user=user,
            message=message,
            timestamp=timestamp,
        )


class EntryUowRepository(repository.Repository[EntryUnitOfWork]):
    EntityNotFound = errors.EntryRepoNotFound
    pass


class EntryUowRepositoryUnitOfWork(unit_of_work.UnitOfWork[EntryUowRepository]):
    def __init__(
        self,
        *,
        event_bus: events.EventBus,
        entry_uow_factory: EntryRepositoryUnitOfWorkFactory,
    ):
        unit_of_work.UnitOfWork.__init__(self, event_bus)
        self._entry_uow_factory = entry_uow_factory

    @property
    def factory(self) -> EntryRepositoryUnitOfWorkFactory:
        return self._entry_uow_factory
