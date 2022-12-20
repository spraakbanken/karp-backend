import logging
from typing import List

from karp.foundation import value_objects
from karp.auth.domain.entities.user import User
from karp.auth.domain import auth_service


logger = logging.getLogger(__name__)


class DummyAuthService(auth_service.AuthService):
    def __init__(self):
        logger.warning("Using DummyAuthService: Don't use this in production!")

    def authenticate(self, scheme: str, credentials: str) -> User:
        return User(credentials or "dummy", {}, {})

    def authorize(
        self,
        level: value_objects.PermissionLevel,
        user: User,
        resource_ids: List[str],
    ) -> bool:
        return True
