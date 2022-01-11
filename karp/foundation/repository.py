import abc
import uuid
from typing import Generic, TypeVar, Optional, Type, Union

from .errors import NotFoundError

EntityType = TypeVar("EntityType")


class Repository(Generic[EntityType], abc.ABC):
    EntityNotFound: Type[NotFoundError] = NotFoundError

    def __init__(self):
        self.seen = set()

    def save(self, entity: EntityType):
        self._save(entity)
        self.seen.add(entity)

    @abc.abstractmethod
    def _save(self, entity: EntityType):
        raise NotImplementedError()

    def by_id(
        self, id_: Union[uuid.UUID, str], *, version: Optional[int] = None
    ) -> EntityType:
        entity = self._by_id(id_, version=version)
        if entity:
            self.seen.add(entity)
        else:
            raise self.EntityNotFound(f"Entity with id={id_} is not found")
        return entity

    get_by_id = by_id

    @abc.abstractmethod
    def _by_id(
        self, id_: Union[uuid.UUID, str], *, version: Optional[int] = None
    ) -> Optional[EntityType]:
        raise NotImplementedError()
