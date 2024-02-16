import logging  # noqa: F811
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.param_functions import Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, SecurityScopes
from fastapi.security import utils as security_utils

from karp import auth, lex
from karp.auth.domain.errors import TokenError
from karp.auth_infrastructure import (
    JWTAuthService,
    ResourcePermissionQueries,
)
from karp.lex.application.repositories import ResourceRepository
from karp.main.errors import KarpError  # noqa: F401

from . import lex_deps
from .fastapi_injector import inject_from_req

# auto_error false is needed so that FastAPI does not
# give back a faulty 403 when credentials are missing
auth_scheme = HTTPBearer(auto_error=False)

logger = logging.getLogger(__name__)


def bearer_scheme(authorization=Header(None)):  # noqa: ANN201, D103
    if not authorization:
        return None
    scheme, credentials = security_utils.get_authorization_scheme_param(authorization)
    if not (scheme and credentials):
        return None
    return HTTPAuthorizationCredentials(scheme=scheme, credentials=credentials)


def get_resource_permissions(  # noqa: D103
    resources: ResourceRepository = Depends(lex_deps.get_resource_repository),
) -> ResourcePermissionQueries:
    return ResourcePermissionQueries(resources)


get_auth_service = inject_from_req(JWTAuthService)


# TODO this one uses "bearer_scheme"
# get_user uses "auth_scheme"
# can this one call get_user with same creds?
def get_user_optional(  # noqa: D103
    security_scopes: SecurityScopes,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    auth_service: JWTAuthService = Depends(get_auth_service),
) -> Optional[auth.User]:
    if not credentials:
        return None
    return get_user(security_scopes, credentials, auth_service)


def get_user(  # noqa: D103
    security_scopes: SecurityScopes,
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
    auth_service: JWTAuthService = Depends(get_auth_service),
) -> auth.User:
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    if not credentials:
        raise credentials_exception
    try:
        logger.debug(
            "Calling auth_service",
            extra={"credentials": credentials},
        )
        return auth_service.authenticate(credentials.scheme, credentials.credentials)
    except KarpError as err:
        raise credentials_exception from err
    except TokenError as err:
        raise credentials_exception from err
