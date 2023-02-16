import abc  # noqa: D100, I001
import logging
from typing import List, Optional  # noqa: F401

from karp.foundation import value_objects
from karp.auth.domain import errors  # noqa: F401
from karp.auth.domain.entities.user import User


logger = logging.getLogger("karp")


class AuthServiceConfig:  # noqa: D101
    pass


class AuthService(abc.ABC):  # noqa: D101
    @abc.abstractmethod
    def authenticate(self, scheme: str, credentials: str) -> User:  # noqa: D102
        return User("dummy", {}, {})

    @abc.abstractmethod
    def authorize(  # noqa: D102
        self,
        level: value_objects.PermissionLevel,
        user: User,
        resource_ids: List[str],
    ) -> bool:
        return True
