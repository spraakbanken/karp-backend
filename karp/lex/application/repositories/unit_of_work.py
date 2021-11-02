"""Unit of Work"""
import abc
import logging
from typing import Dict, Optional, Iterable
from functools import singledispatch

from karp.foundation import entity
from karp.foundation.events import EventBus
from karp.foundation.unit_of_work import UnitOfWork
from karp.lex.application import repositories


logger = logging.getLogger("karp")


class ResourceUnitOfWork(UnitOfWork[repositories.ResourceRepository]):
    def __init__(self, event_bus: EventBus):
        UnitOfWork.__init__(self, event_bus)

    @property
    def resources(self) -> repositories.ResourceRepository:
        return self.repo


class EntryUnitOfWork(
    UnitOfWork[repositories.EntryRepository],
    entity.TimestampedEntity,
):
    repository_type: str

    def __init__(
        self,
        name: str,
        config: Dict,
        connection_str: Optional[str],
        message: str,
        event_bus: EventBus,
        *args,
        **kwargs,
    ):
        UnitOfWork.__init__(self, event_bus)
        entity.TimestampedEntity.__init__(
            self, *args, **kwargs)
        self._name = name
        self._connection_str = connection_str
        self._config = config
        self._message = message

    @property
    def entries(self) -> repositories.EntryRepository:
        return self.repo

    @property
    def name(self) -> str:
        return self._name

    @property
    def connection_str(self) -> Optional[str]:
        return self._connection_str

    @property
    def config(self) -> Dict:
        return self._config

    @property
    def message(self) -> str:
        return self._message


class EntriesUnitOfWork:
    def __init__(self, entry_uows=None):
        self.entry_uows: Dict[str, EntryUnitOfWork] = (
            {key: uow for key, uow in entry_uows} if entry_uows else {}
        )

    def get(self, resource_id: str) -> EntryUnitOfWork:
        return self.entry_uows[resource_id]

    def get_uow(self, resource_id: str) -> EntryUnitOfWork:
        return self.entry_uows[resource_id]

    def set_uow(self, resource_id: str, uow: EntryUnitOfWork):
        self.entry_uows[resource_id] = uow

    @property
    def repo(self):
        return self

    def collect_new_events(self) -> Iterable:
        for uow in self.entry_uows.values():
            yield from uow.collect_new_events()


class EntryUowFactory(abc.ABC):
    @abc.abstractmethod
    def create(
        self,
        resource_id: str,
        resource_config: Dict,
        entry_repositories_settings: Optional[Dict],
    ) -> EntryUnitOfWork:
        raise NotImplementedError


class DefaultEntryUowFactory(EntryUowFactory):
    def create(
        self,
        resource_id: str,
        resource_config: Dict,
        entry_repositories_settings: Optional[Dict],
    ) -> EntryUnitOfWork:
        entry_repositories_type = resource_config["entry_repositories_type"]
        if not entry_repositories_settings:
            entry_repositories_settings = (
                repositories.EntryRepository.create_repositories_settings(
                    resource_id=resource_id,
                    repositories_type=entry_repositories_type,
                    resource_config=resource_config,
                )
            )
        # entry_repositories = repositories.EntryRepository.create(
        #     entry_repositories_type, settings=entry_repositories_settings
        # )
        return EntryUnitOfWork.create(
            entry_repositories_type=entry_repositories_type,
            settings=entry_repositories_settings,
            resource_config=resource_config,
        )
        # return create_entry_unit_of_work(entry_repositories)


@singledispatch
def create_entry_unit_of_work(repo) -> EntryUnitOfWork:
    raise NotImplementedError(f"Can't handle repositories '{repo!r}'")
