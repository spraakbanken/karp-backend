"""Module for jwt-based authentication."""
from pathlib import Path
import time
from typing import List

import jwt
import jwt.exceptions as jwte  # pyre-ignore

from karp.domain.auth_service import AuthService, PermissionLevel
from karp.domain.models.user import User
from karp.domain.errors import AuthError
from karp.application import config

# from karp.infrastructure.unit_of_work import unit_of_work

# import karp.resourcemgr as resourcemgr
from karp.errors import KarpError, ClientErrorCodes


def load_jwt_key(path: Path) -> str:
    with open(path) as fp:
        return fp.read()


jwt_key = load_jwt_key(config.JWT_AUTH_PUBKEY_PATH)


class JWTAuthenticator(AuthService):
    def __init__(self) -> None:
        print("JWTAuthenticator created")

    def authenticate(self, _scheme: str, credentials: str) -> User:
        print("JWTAuthenticator.authenticate: called")

        try:
            user_token = jwt.decode(credentials, key=jwt_key, algorithms=["RS256"])
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

    def authorize(self, level: PermissionLevel, user: User, resource_ids: List[str]):

        with unit_of_work(using=ctx.resource_repo) as resources_uw:
            for resource_id in resource_ids:
                resource = resources_uw.by_resource_id(resource_id)
                if resource.is_protected(resource_id, level) and (
                    not user
                    or not user.permissions.get(resource_id)
                    or user.permissions[resource_id] < user.levels[level]
                ):
                    return False
        return True
