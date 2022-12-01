import abc
import ulid
from typing import Generic, TypeVar, Optional, Type, Union

from karp.foundation.value_objects import unique_id
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

    def _check_id_has_correct_type(self, id_) -> None:
        if not isinstance(id_, unique_id.UniqueId):
            raise ValueError(f"expected UniqueId, got '{id_}' (type: ´{type(id_)}')")

    def _ensure_correct_id_type(self, v) -> unique_id.UniqueId:
        try:
            return unique_id.parse(v)
        except ValueError as exc:
            raise ValueError(
                f"expected valid UniqueId, got '{v}' (type: ´{type(v)}')"
            ) from exc

    def by_id(
        self, id_: unique_id.UniqueId, *, version: Optional[int] = None, **kwargs
    ) -> EntityType:
        # self._check_id_has_correct_type(id_)
        entity = self._by_id(self._ensure_correct_id_type(id_), version=version)
        if entity:
            self.seen.add(entity)
        else:
            raise self.EntityNotFound(f"Entity with id={id_} is not found")
        return entity

    get_by_id = by_id

    def get_by_id_optional(
        self, id_: unique_id.UniqueId, *, version: Optional[int] = None, **kwargs
    ) -> Optional[EntityType]:
        # self._check_id_has_correct_type(id_)
        entity = self._by_id(self._ensure_correct_id_type(id_), version=version)
        if entity:
            self.seen.add(entity)
        return entity

    @abc.abstractmethod
    def _by_id(
        self,
        id_: Union[unique_id.UniqueId, ulid.ULID, str],
        *,
        version: Optional[int] = None,
        **kwargs,
    ) -> Optional[EntityType]:
        raise NotImplementedError()

    @abc.abstractmethod
    def num_entities(self) -> int:
        ...
