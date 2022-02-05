"""Module for jwt-based authentication."""
import time
from pathlib import Path
from typing import Dict, List, Optional

import jwt
import jwt.exceptions as jwte  # pyre-ignore
import pydantic


from karp.foundation import value_objects
from karp.auth.application.queries import IsResourceProtected
from karp.auth.domain.errors import ExpiredToken, TokenError, InvalidTokenPayload
from karp.auth.domain.entities.user import User
from karp.auth.domain import auth_service



class JWTMeta(pydantic.BaseModel):
    iss: str
    aud: Optional[str]
    iat: float
    exp: float


class JWTCreds(pydantic.BaseModel):
    sub: str
    levels: Dict
    scope: Optional[Dict]


class JWTPayload(JWTMeta, JWTCreds):
    pass


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
            raise ExpiredToken() from exc
        except jwte.DecodeError as exc:
            raise TokenError() from exc

        try:
            payload = JWTPayload(**user_token)
        except pydantic.ValidationError as exc:
            print(f'{exc=}')
            raise InvalidTokenPayload() from exc

        lexicon_permissions = {}
        if payload.scope and "lexica" in payload.scope:
            lexicon_permissions = payload.scope['lexica']
        return User(
            payload.sub,
            lexicon_permissions,
            payload.levels
        )

    def authorize(
        self,
        level: value_objects.PermissionLevel,
        user: User,
        resource_ids: List[str],
    ):
        return not any(
            self.is_resource_protected.query(resource_id, level)
            and (
                not user
                or not user.has_enough_permissions(resource_id, level)
            ) for resource_id in resource_ids
        )
