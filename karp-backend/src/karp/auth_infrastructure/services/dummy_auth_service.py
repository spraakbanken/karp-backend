import logging  # noqa: D100, I001
from typing import List

from karp.foundation import value_objects
from karp.auth.domain.entities.user import User
from karp.auth.domain import auth_service


logger = logging.getLogger(__name__)


class DummyAuthService(auth_service.AuthService):  # noqa: D101
    def __init__(self):  # noqa: D107, ANN204
        logger.warning("Using DummyAuthService: Don't use this in production!")

    def authenticate(self, scheme: str, credentials: str) -> User:  # noqa: D102
        return User(credentials or "dummy", {}, {})

    def authorize(  # noqa: D102
        self,
        level: value_objects.PermissionLevel,
        user: User,
        resource_ids: List[str],
    ) -> bool:
        return True
