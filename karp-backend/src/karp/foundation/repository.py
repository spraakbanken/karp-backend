import abc  # noqa: D100, I001
import ulid
from typing import Generic, TypeVar, Optional, Type, Union

from karp.lex_core.value_objects import UniqueId, unique_id
from .errors import NotFoundError

EntityType = TypeVar("EntityType")


class Repository(Generic[EntityType], abc.ABC):  # noqa: D101
    EntityNotFound: Type[NotFoundError] = NotFoundError

    def save(self, entity: EntityType):  # noqa: ANN201, D102
        self._save(entity)

    @abc.abstractmethod
    def _save(self, entity: EntityType):  # noqa: ANN202
        raise NotImplementedError()

    def _check_id_has_correct_type(self, id_) -> None:
        if not isinstance(id_, unique_id.UniqueId):
            raise ValueError(f"expected UniqueId, got '{id_}' (type: `{type(id_)}')")

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
    ) -> EntityType:
        if entity := self._by_id(self._ensure_correct_id_type(id), version=version):
            return entity
        entity_not_found = self.create_entity_not_found(
            f"Entity with id={id} is not found"
        )
        raise entity_not_found

    get_by_id = by_id

    def get_by_id_optional(  # noqa: D102
        self,
        id_: unique_id.UniqueId,
        *,
        version: Optional[int] = None,
        **kwargs,  # noqa: ANN003
    ) -> Optional[EntityType]:
        return self._by_id(self._ensure_correct_id_type(id_), version=version)

    @abc.abstractmethod
    def _by_id(
        self,
        id_: Union[unique_id.UniqueId, ulid.ULID, str],
        *,
        version: Optional[int] = None,
        **kwargs,  # noqa: ANN003
    ) -> Optional[EntityType]:
        raise NotImplementedError()

    @abc.abstractmethod
    def num_entities(self) -> int:  # noqa: D102
        ...

    def create_entity_not_found(self, msg: str) -> Exception:
        """Create EntityNotFound.

        Override this to get preciser traceback.
        """
        return self.EntityNotFound(msg)
