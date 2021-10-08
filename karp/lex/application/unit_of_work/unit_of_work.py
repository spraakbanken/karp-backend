"""Unit of Work"""
import abc
import logging
import typing
from functools import singledispatch

from karp.domain import errors, index, network, repository


logger = logging.getLogger("karp")


class ResourceUnitOfWork(UnitOfWork[repository.ResourceRepository]):
    @property
    def resources(self) -> repository.ResourceRepository:
        return self.repo


class EntryUnitOfWork(UnitOfWork[repository.EntryRepository]):

    @property
    def entries(self) -> repository.EntryRepository:
        return self.repo


class IndexUnitOfWork(UnitOfWork[index.Index]):
    pass


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
        entry_repository_settings: typing.Optional[typing.Dict],
    ) -> EntryUnitOfWork:
        raise NotImplementedError


class DefaultEntryUowFactory(EntryUowFactory):
    def create(
        self,
        resource_id: str,
        resource_config: typing.Dict,
        entry_repository_settings: typing.Optional[typing.Dict],
    ) -> EntryUnitOfWork:
        entry_repository_type = resource_config["entry_repository_type"]
        if not entry_repository_settings:
            entry_repository_settings = (
                repository.EntryRepository.create_repository_settings(
                    resource_id=resource_id,
                    repository_type=entry_repository_type,
                    resource_config=resource_config,
                )
            )
        # entry_repository = repository.EntryRepository.create(
        #     entry_repository_type, settings=entry_repository_settings
        # )
        return EntryUnitOfWork.create(
            entry_repository_type=entry_repository_type,
            settings=entry_repository_settings,
            resource_config=resource_config,
        )
        # return create_entry_unit_of_work(entry_repository)


@singledispatch
def create_entry_unit_of_work(repo) -> EntryUnitOfWork:
    raise NotImplementedError(f"Can't handle repository '{repo!r}'")
