"""Unit of Work"""
import abc
from functools import singledispatch
import logging
import typing

from karp.domain import errors, index, network, repository

RepositoryType = typing.TypeVar(
    "RepositoryType", repository.Repository, index.Index, network.Network
)


logger = logging.getLogger("karp")


class UnitOfWork(typing.Generic[RepositoryType], abc.ABC):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.rollback()

    def commit(self):
        self._commit()

    def collect_new_events(self) -> typing.Iterable:
        for entity in self.repo.seen:
            while entity.events:
                yield entity.events.pop(0)

    @abc.abstractmethod
    def _commit(self):
        pass

    @abc.abstractmethod
    def rollback(self):
        pass

    @property
    @abc.abstractmethod
    def repo(self) -> RepositoryType:
        pass


class ResourceUnitOfWork(UnitOfWork[repository.ResourceRepository]):
    @property
    def resources(self) -> repository.ResourceRepository:
        return self.repo


class EntryUnitOfWork(UnitOfWork[repository.EntryRepository]):
    _registry = {}
    type = None

    def __init_subclass__(
        cls, entry_repository_type: str, is_default: bool = False, **kwargs
    ) -> None:
        super().__init_subclass__(**kwargs)
        print(
            f"""EntryUnitOfWork.__init_subclass__ called with:
            entry_repository_type={entry_repository_type} and
            is_default={is_default}"""
        )
        if entry_repository_type is None:
            raise RuntimeError(
                "Unallowed entry_repository_type: entry_repository_type = None"
            )
        if entry_repository_type in cls._registry:
            raise RuntimeError(
                f"An EntryUnitOfWork with type '{entry_repository_type}' already exists: {cls._registry[entry_repository_type]!r}"
            )

        # if is_default and None in cls._registry:
        #     raise RuntimeError(f"A default EntryRepository is already set. Default type is {cls._registry[None]!r}")
        cls.type = entry_repository_type
        cls._registry[entry_repository_type] = cls
        if is_default or None not in cls._registry:
            logger.info(
                "Setting default EntryUnitOfWork type to '%s'", entry_repository_type
            )
            cls._registry[None] = entry_repository_type

    @classmethod
    def get_default_entry_repository_type(cls) -> typing.Optional[str]:
        return cls._registry[None]

    @classmethod
    def create(
        cls,
        entry_repository_type: typing.Optional[str],
        settings: typing.Dict,
        resource_config: typing.Dict,
        **kwargs,
    ):
        print(f"_registry={cls._registry}")
        if entry_repository_type is None:
            entry_repository_type = cls._registry[None]
        try:
            uow_cls = cls._registry[entry_repository_type]
        except KeyError as err:
            raise errors.ConfigurationError(
                f"Can't create an EntryUnitOfWork with type '{entry_repository_type}'"
            ) from err
        print(f"kwargs = {kwargs}")
        return uow_cls.from_dict(settings, resource_config, **kwargs)

    @property
    def entries(self) -> repository.EntryRepository:
        return self.repo


class IndexUnitOfWork(UnitOfWork[index.Index]):
    _registry = {}
    type = None

    def __init_subclass__(
        cls, index_type: str, is_default: bool = False, **kwargs
    ) -> None:
        super().__init_subclass__(**kwargs)
        print(
            f"""IndexUnitOfWork.__init_subclass__ called with:
            index_type={index_type} and
            is_default={is_default}"""
        )
        if index_type is None:
            raise RuntimeError("Unallowed index_type: index_type = None")
        if index_type in cls._registry:
            raise RuntimeError(
                f"An IndexUnitOfWork with type '{index_type}' already exists: {cls._registry[index_type]!r}"
            )

        # if is_default and None in cls._registry:
        #     raise RuntimeError(f"A default EntryRepository is already set. Default type is {cls._registry[None]!r}")
        cls.type = index_type
        cls._registry[index_type] = cls
        if is_default or None not in cls._registry:
            logger.info("Setting default IndexUnitOfWork type to '%s'", index_type)
            cls._registry[None] = index_type

    @classmethod
    def get_default_index_type(cls) -> typing.Optional[str]:
        return cls._registry[None]

    @classmethod
    def create(
        cls, index_type: typing.Optional[str], **kwargs
    ):  # , settings: typing.Dict, **kwargs):
        print(f"_registry={cls._registry}")
        if index_type is None:
            index_type = cls._registry[None]
        try:
            uow_cls = cls._registry[index_type]
        except KeyError as err:
            raise errors.ConfigurationError(
                f"Can't create an IndexUnitOfWork with type '{index_type}'"
            ) from err
        print(f"kwargs = {kwargs}")
        return uow_cls.from_dict(**kwargs)


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
