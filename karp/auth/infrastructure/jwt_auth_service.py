"""Module for jwt-based authentication."""
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import jwt
import jwt.exceptions as jwte

from karp.auth.domain.errors import ExpiredToken, TokenError
from karp.auth.domain.user import User

logger = logging.getLogger(__name__)


def load_jwt_key(path: Path) -> str:
    with open(path) as fp:
        return fp.read()


class JWTAuthServiceConfig:
    def __init__(self, pubkey_path: str):
        self._pubkey_path = Path(pubkey_path)

    @property
    def pubkey_path(self) -> Path:
        return self._pubkey_path


@dataclass
class JWTPayload:
    sub: str
    levels: Dict
    scope: Optional[Dict]


class JWTAuthService:
    def __init__(self, pubkey_path: Path) -> None:
        self._jwt_key = load_jwt_key(pubkey_path)
        logger.debug("JWTAuthenticator created")

    def authenticate(self, credentials: str) -> User:
        logger.debug("authenticate called", extra={"credentials": credentials})

        try:
            jwt_decoded = jwt.decode(
                credentials, key=self._jwt_key, algorithms=["RS256"], leeway=5
            )
            payload = JWTPayload(
                sub=jwt_decoded["sub"],
                levels=jwt_decoded["levels"],
                scope=jwt_decoded.get("scope"),
            )
        except jwte.ExpiredSignatureError as exc:
            raise ExpiredToken() from exc
        except jwte.DecodeError as exc:
            raise TokenError() from exc

        lexicon_permissions = {}
        if payload.scope and "lexica" in payload.scope:
            lexicon_permissions = payload.scope["lexica"]
        return User(payload.sub, lexicon_permissions, payload.levels)
