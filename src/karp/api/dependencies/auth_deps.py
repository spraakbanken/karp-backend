import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.param_functions import Header
from fastapi.security import APIKeyQuery, HTTPAuthorizationCredentials, HTTPBearer
from fastapi.security import utils as security_utils

from karp import auth
from karp.auth.domain.errors import AuthError
from karp.auth.infrastructure import api_key_service, jwt_auth_service

# auto_error false is needed so that FastAPI does not
# give back a faulty 403 when credentials are missing
auth_scheme = HTTPBearer(auto_error=False)
api_key_scheme = APIKeyQuery(auto_error=False, name="api_key")

logger = logging.getLogger(__name__)


def bearer_scheme(authorization=Header(None)):
    if not authorization:
        return None
    scheme, credentials = security_utils.get_authorization_scheme_param(authorization)
    if not (scheme and credentials):
        return None
    return HTTPAuthorizationCredentials(scheme=scheme, credentials=credentials)


def get_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    api_key: Optional[str] = Depends(api_key_scheme),
) -> Optional[auth.User]:
    if not credentials and not api_key:
        return None
    return get_user(credentials, api_key)


def get_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(auth_scheme),
    api_key: Optional[str] = Depends(api_key_scheme),
) -> auth.User:
    if not credentials and not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing credentials",
        )

    try:
        if credentials:
            logger.debug(
                "Calling auth_service",
                extra={"credentials": credentials},
            )
            return jwt_auth_service.authenticate(credentials.credentials)
        else:
            return api_key_service.authenticate(api_key)
    except AuthError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from err
