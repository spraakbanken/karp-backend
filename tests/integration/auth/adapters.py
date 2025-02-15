"""Unit tests for JWTAuthenticator"""

from datetime import timedelta  # noqa: I001
from typing import Dict, Optional
import os

import jwt

import pathlib
from karp.foundation.timings import utc_now

AUTH_JWT_AUDIENCE = "spraakbanken:auth"

PRIVATE_KEY_PATH = os.environ.get("TEST_AUTH_JWT_PRIVATE_KEY_PATH", "assets/testing/private_key.pem")

jwt_private_key = pathlib.Path(PRIVATE_KEY_PATH).read_text()


def create_access_token(
    user: str,
    levels: Optional[Dict],
    scope: Optional[Dict] = None,
    priv_key: Optional[str] = None,
    audience: str = AUTH_JWT_AUDIENCE,
    expires_in: int | None = None,
) -> str:
    priv_key = priv_key or jwt_private_key
    expires_in = expires_in or 60

    iat = utc_now()
    time_delta = timedelta(minutes=abs(expires_in)).total_seconds()
    exp = iat - time_delta if expires_in < 0 else iat + time_delta
    token_payload = {
        "iss": "spraakbanken.gu.se",
        "iat": iat,
        "exp": exp,
    }
    if audience:
        token_payload["audience"] = audience
    if user:
        token_payload["sub"] = user
    if levels is not None:
        token_payload["levels"] = levels
    if scope:
        token_payload["scope"] = scope

    return jwt.encode(token_payload, priv_key, algorithm="RS256")
