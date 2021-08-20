import abc
from enum import Enum
from karp.services import context
from typing import List

from karp.domain.models.user import User
from karp.services import context


class PermissionLevel(str, Enum):
    write = "write"
    read = "read"
    admin = "admin"


class AuthService(abc.ABC):
    @abc.abstractmethod
    def authenticate(self, scheme: str, credentials: str) -> User:
        return User("dummy", {}, {})

    @abc.abstractmethod
    def authorize(
        self,
        level: PermissionLevel,
        user: User,
        resource_ids: List[str],
        ctx: context.Context,
    ) -> bool:
        return True
