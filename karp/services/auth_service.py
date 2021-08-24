import abc
import logging
from typing import List, Optional

from karp.domain import model, value_objects, errors
from karp.domain.models.user import User

# from karp.services import context

logger = logging.getLogger("karp")


class AuthService(abc.ABC):
    _registry = {}

    def __init_subclass__(
        cls, auth_service_type: str, is_default: bool = False, **kwargs
    ) -> None:
        super().__init_subclass__(**kwargs)
        auth_service_type = auth_service_type.lower()
        if auth_service_type in cls._registry:
            raise RuntimeError(
                f"An AuthService with type '{auth_service_type}' already exists: {cls._registry[auth_service_type]!r}"
            )
        cls._registry[auth_service_type] = cls
        if is_default or None not in cls._registry:
            logger.info("Setting default AuthService type to '%s'", auth_service_type)
            cls._registry[None] = auth_service_type

    @classmethod
    def create(cls, auth_service_type: Optional[str]):
        if auth_service_type is None:
            auth_service_type = cls._registry[None]
        else:
            auth_service_type = auth_service_type.lower()

        try:
            index_cls = cls._registry[auth_service_type]
        except KeyError as err:
            raise errors.ConfigurationError(
                f"Can't create a AuthService of type '{auth_service_type}'"
            ) from err
        return index_cls()

    @abc.abstractmethod
    def authenticate(self, scheme: str, credentials: str) -> User:
        return User("dummy", {}, {})

    @abc.abstractmethod
    def authorize(
        self,
        level: value_objects.PermissionLevel,
        user: model.User,
        resource_ids: List[str],
        ctx: "context.Context",
    ) -> bool:
        return True
