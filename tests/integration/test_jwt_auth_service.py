"""Unit tests for JWTAuthenticator"""

from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from karp.auth.domain.errors import (
    AuthError,
    ExpiredToken,
)
from karp.auth.infrastructure.jwt_auth_service import (
    JWTAuthService,
)
from tests.integration.auth.adapters import create_access_token

# Generate our key
other_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)

AUTH_JWT_AUDIENCE = "spraakbanken:auth"


@pytest.fixture
def jwt_authenticator() -> JWTAuthService:
    return JWTAuthService(
        pubkey_path=Path("assets/testing/pubkey.pem"),
    )


def test_authenticate_invalid_token(jwt_authenticator) -> None:
    with pytest.raises(AuthError):
        jwt_authenticator.authenticate("invalid")


def test_authenticate_expired_token(jwt_authenticator) -> None:
    token = create_access_token(
        user=None,
        levels={},
        expires_in=-1,
    )

    with pytest.raises(ExpiredToken):
        jwt_authenticator.authenticate(token)


class TestAuthTokens:
    def test_can_create_access_token_successfully(self, jwt_authenticator) -> None:
        access_token = create_access_token(
            user="test_user",
            levels={},
        )
        user = jwt_authenticator.authenticate(access_token)
        assert user is not None
        assert user.identifier == "test_user"
