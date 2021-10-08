"""Unit of Work"""
import abc
import logging
import typing
from functools import singledispatch

from karp.foundation.unit_of_work import UnitOfWork
from karp.lex.application import repositories


logger = logging.getLogger("karp")


class ResourceUnitOfWork(UnitOfWork[repositories.ResourceRepository]):
    @property
    def resources(self) -> repositories.ResourceRepository:
        return self.repo


class EntryUnitOfWork(UnitOfWork[repositories.EntryRepository]):

    @property
    def entries(self) -> repositories.EntryRepository:
        return self.repo


class EntriesUnitOfWork:
    def __init__(self, entry_uows=None):
        self.entry_uows: typing.Dict[str, EntryUnitOfWork] = (
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

    def collect_new_events(self) -> typing.Iterable:
        for uow in self.entry_uows.values():
            yield from uow.collect_new_events()


class EntryUowFactory(abc.ABC):
    @abc.abstractmethod
    def create(
        self,
        resource_id: str,
        resource_config: typing.Dict,
        entry_repositories_settings: typing.Optional[typing.Dict],
    ) -> EntryUnitOfWork:
        raise NotImplementedError


class DefaultEntryUowFactory(EntryUowFactory):
    def create(
        self,
        resource_id: str,
        resource_config: typing.Dict,
        entry_repositories_settings: typing.Optional[typing.Dict],
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
