import abc
from typing import Dict, Protocol, Optional

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
        connection_str: Optional[str],
        user: str,
        message: str,
        timestamp: float,
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
        connection_str: Optional[str],
        user: str,
        message: str,
        timestamp: float,
    ) -> EntryUnitOfWork:
        uow_factory_cls = self._container.get(
            Dict[str, EntryUnitOfWorkCreator]
        )[repository_type]

        uow_factory = self._container.create_object(uow_factory_cls)
        return uow_factory(
            entity_id=entity_id,
            name=name,
            config=config,
            connection_str=connection_str,
            user=user,
            message=message,
            timestamp=timestamp,
        )
