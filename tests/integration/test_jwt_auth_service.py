"""Unit tests for JWTAuthenticator"""

import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from karp.auth.domain.errors import (
    AuthError,
    ExpiredToken,
)
from karp.auth.infrastructure import jwt_auth_service
from tests.integration.auth.adapters import create_access_token

# Generate our key
other_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)


def test_authenticate_invalid_token() -> None:
    with pytest.raises(AuthError):
        jwt_auth_service.authenticate("invalid")


def test_authenticate_expired_token() -> None:
    token = create_access_token(
        user=None,
        levels={},
        expires_in=-1,
    )

    with pytest.raises(ExpiredToken):
        jwt_auth_service.authenticate(token)


class TestAuthTokens:
    def test_can_create_access_token_successfully(self) -> None:
        access_token = create_access_token(
            user="test_user",
            levels={},
        )
        user = jwt_auth_service.authenticate(access_token)
        assert user is not None
        assert user.identifier == "test_user"
