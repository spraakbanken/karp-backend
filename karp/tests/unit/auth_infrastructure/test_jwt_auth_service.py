"""Unit tests for JWTAuthenticator"""
import datetime
from pathlib import Path

import jwt
import pytest

from karp.auth.domain.errors import AuthError
from karp.errors import ClientErrorCodes
from karp.auth_infrastructure.services.jwt_auth_service import JWTAuthService

from karp.tests.unit.auth import adapters

with open(Path(__file__).parent / '..' / '..' / "data/private_key.pem") as fp:
    jwt_private_key = fp.read()


@pytest.fixture
def jwt_authenticator():
    return JWTAuthService(
        pubkey_path=Path("karp/tests/data/pubkey.pem"),
        is_resource_protected=adapters.FakeIsResourceProtected(),
    )


@pytest.mark.skip()
def test_authenticate_invalid_token(jwt_authenticator):
    with pytest.raises(AuthError) as exc_info:
        jwt_authenticator.authenticate("scheme", "invalid")

    assert exc_info.value.code == ClientErrorCodes.AUTH_GENERAL_ERROR


@pytest.mark.skip()
def test_authenticate_expired_token(jwt_authenticator):
    token = jwt.encode(
        {"exp": datetime.datetime(2000, 1, 1)}, jwt_private_key, algorithm="RS256"
    )

    with pytest.raises(AuthError) as exc_info:
        jwt_authenticator.authenticate("scheme", token)

    assert exc_info.value.code == ClientErrorCodes.EXPIRED_JWT
