import abc  # noqa: I001
from typing import Optional, Type

from karp.foundation.value_objects import UniqueId
from .errors import NotFoundError


class Repository(abc.ABC):
    EntityNotFound: Type[NotFoundError] = NotFoundError

    def save(self, entity):
        self._save(entity)

    @abc.abstractmethod
    def _save(self, entity):
        raise NotImplementedError()

    def by_id(
        self,
        id: UniqueId,  # noqa: A002
        *,
        version: Optional[int] = None,
        **kwargs,
    ):
        if entity := self._by_id(id, version=version):
            return entity
        raise self.EntityNotFound(f"Entity with id={id} is not found")

    def by_id_optional(
        self,
        id: UniqueId,  # noqa: A002
        *,
        version: Optional[int] = None,
        **kwargs,
    ) -> Optional:
        return self._by_id(id, version=version)

    @abc.abstractmethod
    def _by_id(
        self,
        id: UniqueId,  # noqa: A002
        *,
        version: Optional[int] = None,
        **kwargs,
    ) -> Optional:
        raise NotImplementedError()
