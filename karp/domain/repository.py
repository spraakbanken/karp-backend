import abc
import logging
import typing
import uuid
from typing import Dict, List, Optional, Tuple, Union

from karp.domain.value_objects import UniqueId

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
    ) -> EntityType:
        entity = self._by_id(id, version=version)
        if entity:
            self.seen.add(entity)
        else:
            raise self.EntityNotFound(f"Entity with id={id} is not found")
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
    ) -> model.Resource:
        resource = self._by_resource_id(resource_id, version=version)
        if resource:
            self.seen.add(resource)
        else:
            raise self.EntityNotFound(
                f"Entity with resource_id='{resource_id}' can't be found.")
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
