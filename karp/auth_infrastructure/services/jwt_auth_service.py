"""Module for jwt-based authentication."""
import time
from pathlib import Path
from typing import List

import jwt
import jwt.exceptions as jwte  # pyre-ignore


from karp.foundation import value_objects
from karp.auth.application.queries import IsResourceProtected
from karp.domain import errors
from karp.domain.errors import AuthError
from karp.auth.domain.entities.user import User
from karp.errors import ClientErrorCodes, KarpError
from karp.auth.domain import auth_service
from karp.lex.application import repositories
from karp.lex.domain.entities import resource
# from karp.infrastructure.repositories import repositories


def load_jwt_key(path: Path) -> str:
    with open(path) as fp:
        return fp.read()


# jwt_key = load_jwt_key(config.JWT_AUTH_PUBKEY_PATH)


class JWTAuthService(
    auth_service.AuthService, auth_service_type="jwt_auth", is_default=True
):
    def __init__(
        self, pubkey_path: Path, is_resource_protected: IsResourceProtected
    ) -> None:
        self._jwt_key = load_jwt_key(pubkey_path)
        self.is_resource_protected = is_resource_protected
        print("JWTAuthenticator created")

    def authenticate(self, _scheme: str, credentials: str) -> User:
        print("JWTAuthenticator.authenticate: called")

        try:
            user_token = jwt.decode(
                credentials, key=self._jwt_key, algorithms=["RS256"]
            )
        except jwte.ExpiredSignatureError as exc:
            raise AuthError(
                "The given jwt have expired", code=ClientErrorCodes.EXPIRED_JWT
            ) from exc
        except jwte.DecodeError as exc:
            raise AuthError("General JWT error") from exc

        lexicon_permissions = {}
        if "scope" in user_token and "lexica" in user_token["scope"]:
            lexicon_permissions = user_token["scope"]["lexica"]
        return User(user_token["sub"], lexicon_permissions, user_token["levels"])

    def authorize(
        self,
        level: value_objects.PermissionLevel,
        user: User,
        resource_ids: List[str],
    ):
        return not any(self.is_resource_protected.query(resource_id, level) and (
            not user
            or not user.has_enough_permissions(resource_id, level)
        ) for resource_id in resource_ids)
