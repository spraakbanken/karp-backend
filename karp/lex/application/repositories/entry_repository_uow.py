import abc
from typing import Dict, Protocol

import injector


from karp.foundation.value_objects import UniqueId
from .unit_of_work import EntryUnitOfWork


class EntryRepositoryUnitOfWorkFactory:
    @abc.abstractmethod
    def create(
        self,
        repository_type: str,
        entity_id: UniqueId,
        name: str,
        config: Dict,
    ) -> EntryUnitOfWork:
        pass


class EntryUnitOfWorkCreator(Protocol):
    def __call__(
        self,
        entity_id: UniqueId,
        name: str,
        config: Dict,
    ) -> EntryUnitOfWork:
        pass


class InjectorEntryUnitOfWorkRepoFactory(
    EntryRepositoryUnitOfWorkFactory
):
    def __init__(self, container: injector.Injector) -> None:
        self._container = container

    def create(
        self,
        repository_type: str,
        entity_id: UniqueId,
        name: str,
        config: Dict,
    ) -> EntryUnitOfWork:
        uow_factory = self._container.get(
            Dict[str, EntryUnitOfWorkCreator]
        )[repository_type]

        return uow_factory(entity_id, name, config)
