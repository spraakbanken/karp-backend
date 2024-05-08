import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.param_functions import Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.security import utils as security_utils

from karp import auth
from karp.auth.application.resource_permission_queries import ResourcePermissionQueries
from karp.auth.domain.errors import AuthError
from karp.auth.infrastructure.jwt_auth_service import JWTAuthService
from karp.lex.infrastructure import ResourceRepository

from . import lex_deps
from .fastapi_injector import inject_from_req

# auto_error false is needed so that FastAPI does not
# give back a faulty 403 when credentials are missing
auth_scheme = HTTPBearer(auto_error=False)

logger = logging.getLogger(__name__)


def bearer_scheme(authorization=Header(None)):
    if not authorization:
        return None
    scheme, credentials = security_utils.get_authorization_scheme_param(authorization)
    if not (scheme and credentials):
        return None
    return HTTPAuthorizationCredentials(scheme=scheme, credentials=credentials)


def get_resource_permissions(
    resources: ResourceRepository = Depends(lex_deps.get_resource_repository),
) -> ResourcePermissionQueries:
    return ResourcePermissionQueries(resources)


get_auth_service = inject_from_req(JWTAuthService)


def get_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    auth_service: JWTAuthService = Depends(get_auth_service),
) -> Optional[auth.User]:
    if not credentials:
        return None
    return get_user(credentials, auth_service)


def get_user(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
    auth_service: JWTAuthService = Depends(get_auth_service),
) -> auth.User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing credentials",
        )
    try:
        logger.debug(
            "Calling auth_service",
            extra={"credentials": credentials},
        )
        return auth_service.authenticate(credentials.credentials)
    except AuthError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from err
