"""Unit tests for JWTAuthenticator"""

from karp.errors import ClientErrorCodes
from karp.domain.errors import AuthError
import pytest

from karp.infrastructure.jwt.jwt_auth_service import JWTAuthenticator


@pytest.fixture
def jwt_authenticator():
    return JWTAuthenticator()


def test_authenticate_invalid_token(jwt_authenticator):
    with pytest.raises(AuthError) as exc_info:
        jwt_authenticator.authenticate("scheme", "invalid")

    assert exc_info.value.code == ClientErrorCodes.AUTH_GENERAL_ERROR