import abc
from typing import List

from karp.domain import model, value_objects
from karp.domain.models.user import User

# from karp.services import context


class AuthService(abc.ABC):
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
