"""Module for jwt-based authentication."""
import logging
from pathlib import Path
from typing import Dict, Optional

import jwt
import jwt.exceptions as jwte
import pydantic

from karp.auth.domain.errors import ExpiredToken, InvalidTokenPayload, TokenError
from karp.auth.domain.user import User

logger = logging.getLogger(__name__)


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


class JWTAuthServiceConfig:
    def __init__(self, pubkey_path: str):
        self._pubkey_path = Path(pubkey_path)

    @property
    def pubkey_path(self) -> Path:  # noqa: D102
        return self._pubkey_path


class JWTAuthService:
    def __init__(  # noqa: D107
        self, pubkey_path: Path
    ) -> None:
        self._jwt_key = load_jwt_key(pubkey_path)
        logger.debug("JWTAuthenticator created")

    def authenticate(self, _scheme: str, credentials: str) -> User:  # noqa: D102
        logger.debug("authenticate called", extra={"credentials": credentials})

        try:
            user_token = jwt.decode(
                credentials, key=self._jwt_key, algorithms=["RS256"], leeway=5
            )
        except jwte.ExpiredSignatureError as exc:
            raise ExpiredToken() from exc
        except jwte.DecodeError as exc:
            raise TokenError() from exc

        try:
            payload = JWTPayload(**user_token)
        except pydantic.ValidationError as exc:
            raise InvalidTokenPayload() from exc

        lexicon_permissions = {}
        if payload.scope and "lexica" in payload.scope:
            lexicon_permissions = payload.scope["lexica"]
        return User(payload.sub, lexicon_permissions, payload.levels)
