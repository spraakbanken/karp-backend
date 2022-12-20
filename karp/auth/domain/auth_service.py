import abc
import logging
from typing import List, Optional

from karp.foundation import value_objects
from karp.auth.domain import errors
from karp.auth.domain.entities.user import User


logger = logging.getLogger("karp")


class AuthServiceConfig:
    pass


class AuthService(abc.ABC):
    @abc.abstractmethod
    def authenticate(self, scheme: str, credentials: str) -> User:
        return User("dummy", {}, {})

    @abc.abstractmethod
    def authorize(
        self,
        level: value_objects.PermissionLevel,
        user: User,
        resource_ids: List[str],
    ) -> bool:
        return True
