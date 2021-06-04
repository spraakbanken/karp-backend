from typing import List

from karp.application import config

from karp.domain.models.user import User
from karp.domain.auth_service import (
    AuthService,
    PermissionLevel,
)


class DummyAuthService(AuthService):
    def __init__(self):
        pass
        # if False or config.TESTING or config.DEBUG:
        #     raise RuntimeError("Don't use this in production!")

    def authenticate(self, scheme: str, credentials: str) -> User:
        return User(credentials or "dummy", {}, {})

    def authorize(
        self, level: PermissionLevel, user: User, resource_ids: List[str]
    ) -> bool:
        return True
