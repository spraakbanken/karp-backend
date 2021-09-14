"""Unit tests for JWTAuthenticator"""
import datetime
from pathlib import Path

import pytest

import jwt

from karp.errors import ClientErrorCodes
from karp.domain.errors import AuthError

from karp.infrastructure.jwt.jwt_auth_service import JWTAuthenticator
from . import adapters

with open(Path(__file__).parent / ".." / "data/private_key.pem") as fp:
    jwt_private_key = fp.read()


@pytest.fixture
def jwt_authenticator():
    return JWTAuthenticator(
        pubkey_path=Path("karp/tests/data/pubkey.pem"),
        resource_uow=adapters.FakeResourceUnitOfWork(),
    )


def test_authenticate_invalid_token(jwt_authenticator):
    with pytest.raises(AuthError) as exc_info:
        jwt_authenticator.authenticate("scheme", "invalid")

    assert exc_info.value.code == ClientErrorCodes.AUTH_GENERAL_ERROR


def test_authenticate_expired_token(jwt_authenticator):
    token = jwt.encode(
        {"exp": datetime.datetime(2000, 1, 1)}, jwt_private_key, algorithm="RS256"
    )

    with pytest.raises(AuthError) as exc_info:
        jwt_authenticator.authenticate("scheme", token)

    assert exc_info.value.code == ClientErrorCodes.EXPIRED_JWT
