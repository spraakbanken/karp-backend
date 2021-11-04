import logging
from typing import Optional

from dependency_injector import wiring
from fastapi import Depends, HTTPException, status
from fastapi.param_functions import Header
from fastapi.security import (HTTPAuthorizationCredentials, HTTPBearer,
                              SecurityScopes)
from fastapi.security import utils as security_utils

# from karp import bootstrap, services
from karp import auth
# from karp.auth.auth import auth
from karp.errors import ClientErrorCodes, KarpError
from karp.auth.domain.auth_service import AuthService
from .fastapi_injector import inject_from_req
# from .containers import WebAppContainer

# bus = bootstrap.bootstrap()


auth_scheme = HTTPBearer()

logger = logging.getLogger("karp")


def bearer_scheme(authorization=Header(None)):
    if not authorization:
        return None
    # authorization: str = authorization.get("Authorization")
    scheme, credentials = security_utils.get_authorization_scheme_param(authorization)
    if not (scheme and credentials):
        return None
    return HTTPAuthorizationCredentials(scheme=scheme, credentials=credentials)


@wiring.inject
def get_current_user(
    security_scopes: SecurityScopes,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    auth_service: AuthService = Depends(inject_from_req(AuthService)),
) -> Optional[auth.User]:
    if not credentials:
        return None
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
        # code=ClientErrorCodes.NOT_PERMITTED,
    )
    try:
        logger.debug(
            "webapp.app_config.get_current_user: Calling auth_service with credentials = %s",
            credentials,
        )
        return auth_service.authenticate(credentials.scheme, credentials.credentials)
    except KarpError:
        raise credentials_exception
