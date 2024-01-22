import abc  # noqa: D100, I001
from typing import Generic, TypeVar, Optional, Type

from karp.lex_core.value_objects import UniqueId, unique_id
from .errors import NotFoundError


class Repository(abc.ABC):  # noqa: D101
    EntityNotFound: Type[NotFoundError] = NotFoundError

    def save(self, entity):  # noqa: ANN201, D102
        self._save(entity)

    @abc.abstractmethod
    def _save(self, entity):  # noqa: ANN202
        raise NotImplementedError()

    def _ensure_correct_id_type(self, v) -> unique_id.UniqueId:
        try:
            return unique_id.UniqueId.validate(v)
        except ValueError as exc:
            raise ValueError(
                f"expected valid UniqueId, got '{v}' (type: `{type(v)}')"
            ) from exc

    def by_id(  # noqa: D102
        self,
        id: UniqueId,  # noqa: A002
        *,
        version: Optional[int] = None,
        **kwargs,  # noqa: ANN003
    ):
        if entity := self._by_id(id, version=version):
            return entity
        raise self.EntityNotFound(f"Entity with id={id} is not found")

    get_by_id = by_id

    def get_by_id_optional(  # noqa: D102
        self,
        id: UniqueId,  # noqa: A002
        *,
        version: Optional[int] = None,
        **kwargs,  # noqa: ANN003
    ) -> Optional:
        return self._by_id(id, version=version)

    @abc.abstractmethod
    def _by_id(
        self,
        id: UniqueId,  # noqa: A002
        *,
        version: Optional[int] = None,
        **kwargs,  # noqa: ANN003
    ) -> Optional:
        raise NotImplementedError()
