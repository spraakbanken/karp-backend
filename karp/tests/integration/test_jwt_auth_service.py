"""Unit tests for JWTAuthenticator"""
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Type

import jwt
import pydantic
import pytest

from karp.foundation.time import utc_now
from karp.auth.domain.errors import (
    AuthError,
    ExpiredToken,
    InvalidTokenSignature,
    InvalidTokenAudience,
    InvalidTokenPayload,
    TokenError,
)
from karp.errors import ClientErrorCodes
from karp.auth_infrastructure.services.jwt_auth_service import (
    JWTAuthService,
    JWTCreds,
    JWTMeta,
    JWTPayload,
)

from karp.main.config import AUTH_JWT_AUDIENCE
from karp.tests.unit.auth import adapters
from karp.tests.integration.auth.adapters import create_access_token
from cryptography.hazmat.primitives.asymmetric import rsa

# Generate our key

other_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)


@pytest.fixture
def jwt_authenticator():
    return JWTAuthService(
        pubkey_path=Path("karp/tests/data/pubkey.pem"),
        is_resource_protected=adapters.InMemoryIsResourceProtected(),
    )


def test_authenticate_invalid_token(jwt_authenticator):
    with pytest.raises(AuthError):
        jwt_authenticator.authenticate("scheme", "invalid")


def test_authenticate_expired_token(jwt_authenticator):
    token = create_access_token(
        user=None,
        levels={},
        expires_in=-1,
    )

    with pytest.raises(ExpiredToken):
        jwt_authenticator.authenticate("scheme", token)


class TestAuthTokens:
    def test_can_create_access_token_successfully(self, jwt_authenticator) -> None:
        access_token = create_access_token(
            user="test_user",
            levels={},
        )
        user = jwt_authenticator.authenticate("bearer", access_token)
        assert user is not None
        assert user.identifier == "test_user"

    def test_token_missing_user_is_invalid(self, jwt_authenticator) -> None:
        access_token = create_access_token(
            user=None,
            levels={},
        )
        with pytest.raises(TokenError):
            jwt_authenticator.authenticate("bearer", access_token)

    @pytest.mark.parametrize(
        "user, levels, secret_key, jwt_audience, exception",
        (
            ("user", {}, other_key, AUTH_JWT_AUDIENCE, TokenError),
            ("user", None, None, AUTH_JWT_AUDIENCE, InvalidTokenPayload),
            pytest.param(
                "user",
                {},
                None,
                "othersite:auth",
                InvalidTokenAudience,
                marks=pytest.mark.xfail(reason="audience not impl on auth"),
            ),
            (None, {}, None, AUTH_JWT_AUDIENCE, InvalidTokenPayload),
        ),
    )
    def test_invalid_token_content_raises_error(
        self,
        jwt_authenticator,
        user: str,
        levels: Optional[Dict],
        secret_key: Optional[str],
        jwt_audience: str,
        exception: Type[BaseException],
    ) -> None:
        with pytest.raises(exception):
            access_token = create_access_token(
                user=user,
                levels=levels,
                priv_key=secret_key,
                audience=jwt_audience,
            )
            jwt_authenticator.authenticate("bearer", access_token)
