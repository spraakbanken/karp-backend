import abc
from karp.utility.unique_id import UniqueId
import logging
import typing
from typing import Dict, List, Optional, Union, Tuple
import uuid

from . import errors, model

logger = logging.getLogger("karp")

EntityType = typing.TypeVar("EntityType")


class Repository(typing.Generic[EntityType], abc.ABC):
    EntityNotFound = RuntimeError

    def __init__(self):
        print("init seen")
        self.seen = set()

    def put(self, entity: EntityType):
        self._put(entity)
        self.seen.add(entity)

    def update(self, entity: EntityType):
        existing_entity = self.by_id(entity.id)
        if not existing_entity:
            raise self.EntityNotFound(entity)
        self.seen.add(entity)
        self._update(entity)

    @abc.abstractmethod
    def _put(self, entity: EntityType):
        raise NotImplementedError()

    @abc.abstractmethod
    def _update(self, entity: EntityType):
        raise NotImplementedError()

    def by_id(
        self, id: Union[uuid.UUID, str], *, version: Optional[int] = None
    ) -> Optional[EntityType]:
        entity = self._by_id(id, version=version)
        if entity:
            self.seen.add(entity)
        return entity

    @abc.abstractmethod
    def _by_id(
        self, id: Union[uuid.UUID, str], *, version: Optional[int] = None
    ) -> Optional[EntityType]:
        raise NotImplementedError()


class ResourceRepository(Repository[model.Resource]):
    EntityNotFound = errors.ResourceNotFound

    @abc.abstractmethod
    def check_status(self):
        pass

    @abc.abstractmethod
    def resource_ids(self) -> typing.Iterable[str]:
        raise NotImplementedError()

    def by_resource_id(
        self, resource_id: str, *, version: Optional[int] = None
    ) -> Optional[model.Resource]:
        resource = self._by_resource_id(resource_id, version=version)
        if resource:
            self.seen.add(resource)
        return resource

    @abc.abstractmethod
    def _by_resource_id(
        self, resource_id: str, *, version: Optional[int] = None
    ) -> Optional[model.Resource]:
        raise NotImplementedError()

    # @abc.abstractmethod
    # def resources_with_id(self, resource_id: str):
    #     raise NotImplementedError()

    # @abc.abstractmethod
    # def resource_with_id_and_version(self, resource_id: str, version: int):
    #     raise NotImplementedError()

    # @abc.abstractmethod
    # def get_active_resource(self, resource_id: str) -> Optional[Resource]:
    #     raise NotImplementedError()

    def get_published_resources(self) -> typing.List[model.Resource]:
        published_resources = []
        for resource in self._get_published_resources():
            self.seen.add(resource)
            published_resources.append(resource)
        return published_resources

    @abc.abstractmethod
    def _get_published_resources(self) -> typing.Iterable[model.Resource]:
        raise NotImplementedError()


class EntryRepository(Repository[model.Entry]):
    # class Repository:
    #     def __init_subclass__(cls) -> None:
    #         print(f"Setting EntryRepository.repository = {cls}")
    #         EntryRepository.repository = cls

    #     def by_id(id: UUID):
    #         raise NotImplementedError()

    _registry = {}
    type = None
    repository = None

    def __init_subclass__(
        cls, repository_type: str, is_default: bool = False, **kwargs
    ) -> None:
        super().__init_subclass__(**kwargs)
        print(
            f"""EntryRepository.__init_subclass__ called with:
            repository_type={repository_type} and
            is_default={is_default}"""
        )
        if repository_type is None:
            raise RuntimeError("Unallowed repository_type: repository_type = None")
        if repository_type in cls._registry:
            raise RuntimeError(
                f"An EntryRepository with type '{repository_type}' already exists: {cls._registry[repository_type]!r}"
            )

        # if is_default and None in cls._registry:
        #     raise RuntimeError(f"A default EntryRepository is already set. Default type is {cls._registry[None]!r}")
        cls.type = repository_type
        cls._registry[repository_type] = cls
        if is_default or None not in cls._registry:
            logger.info("Setting default EntryRepository type to '%s'", repository_type)
            cls._registry[None] = repository_type

    @classmethod
    def get_default_repository_type(cls) -> Optional[str]:
        return cls._registry[None]

    @classmethod
    def create(cls, repository_type: Optional[str], settings: Dict, **kwargs):
        print(f"_registry={cls._registry}")
        if repository_type is None:
            repository_type = cls._registry[None]
        try:
            repository_cls = cls._registry[repository_type]
        except KeyError:
            raise errors.ConfigurationError(
                f"Can't create an EntryRepository with type '{repository_type}'"
            )
        print(f"kwargs = {kwargs}")
        return repository_cls.from_dict(settings, **kwargs)

    @classmethod
    def create_repository_settings(
        cls,
        repository_type: Optional[str],
        resource_id: str,
        resource_config: typing.Dict,
    ) -> Dict:
        if repository_type is None:
            repository_type = cls.get_default_repository_type()
        repository_cls = cls._registry[repository_type]
        return repository_cls._create_repository_settings(resource_id, resource_config)

    @classmethod
    @abc.abstractmethod
    def from_dict(cls, settings: Dict):
        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def _create_repository_settings(
        cls, resource_id: str, resource_config: typing.Dict
    ):
        raise NotImplementedError()

    def __init__(self):
        super().__init__()
        self.settings = {}

    def by_id(
        self,
        id_: UniqueId,
        *,
        version: Optional[int] = None,
        after_date: Optional[float] = None,
        before_date: Optional[float] = None,
        oldest_first: bool = False,
    ) -> model.Entry:
        entry = self._by_id(
            id_,
            version=version,
            after_date=after_date,
            before_date=before_date,
            oldest_first=oldest_first,
        )
        if entry:
            self.seen.add(entry)
            return entry
        raise errors.EntryNotFound(id_=id_)

    @abc.abstractmethod
    def _by_id(
        self,
        id: UniqueId,
        *,
        version: Optional[int] = None,
        after_date: Optional[float] = None,
        before_date: Optional[float] = None,
        oldest_first: bool = False,
    ) -> typing.Optional[model.Entry]:
        raise NotImplementedError()

    # @abc.abstractmethod
    def move(self, entry: model.Entry, *, old_entry_id: str):
        raise NotImplementedError()

    # @abc.abstractmethod
    def delete(self, entry: model.Entry):
        raise NotImplementedError()

    # @abc.abstractmethod
    def entry_ids(self) -> List[str]:
        raise NotImplementedError()

    def by_entry_id(
        self, entry_id: str, *, version: Optional[int] = None
    ) -> model.Entry:
        entry = self._by_entry_id(entry_id, version=version)
        if entry:
            self.seen.add(entry)
            return entry
        raise errors.EntryNotFound(entry_id=entry_id)

    @abc.abstractmethod
    def _by_entry_id(
        self, entry_id: str, *, version: Optional[int] = None
    ) -> Optional[model.Entry]:
        raise NotImplementedError()

    # @abc.abstractmethod
    def teardown(self):
        """Use for testing purpose."""
        return

    # @abc.abstractmethod
    # def by_referenceable(self, filters: Optional[Dict] = None, **kwargs) -> List[Entry]:
    #     raise NotImplementedError()

    # @abc.abstractmethod
    def get_history(
        self,
        user_id: Optional[str] = None,
        entry_id: Optional[str] = None,
        from_date: Optional[float] = None,
        to_date: Optional[float] = None,
        from_version: Optional[int] = None,
        to_version: Optional[int] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Tuple[List[model.Entry], int]:
        return [], 0

    @abc.abstractmethod
    def all_entries(self) -> typing.Iterable[model.Entry]:
        """Return all entries."""
        return []
