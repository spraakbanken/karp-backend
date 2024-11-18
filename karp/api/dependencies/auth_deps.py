import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.param_functions import Header
from fastapi.security import APIKeyQuery, HTTPAuthorizationCredentials, HTTPBearer
from fastapi.security import utils as security_utils

from karp import auth
from karp.auth.application.resource_permission_queries import ResourcePermissionQueries
from karp.auth.domain.errors import AuthError
from karp.auth.infrastructure.jwt_auth_service import JWTAuthService
from karp.lex.infrastructure import ResourceRepository

from ...auth.infrastructure import APIKeyService
from . import lex_deps
from .fastapi_injector import inject_from_req

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


def get_resource_permission_queries(
    resources: ResourceRepository = Depends(lex_deps.get_resource_repository),
) -> ResourcePermissionQueries:
    return ResourcePermissionQueries(resources)


get_auth_service = inject_from_req(JWTAuthService)
get_api_key_service = inject_from_req(APIKeyService)


def get_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    api_key: Optional[str] = Depends(api_key_scheme),
    auth_service: JWTAuthService = Depends(get_auth_service),
    api_key_service: APIKeyService = Depends(get_api_key_service),
) -> Optional[auth.User]:
    if not credentials and not api_key:
        return None
    return get_user(credentials, api_key, auth_service, api_key_service)


def get_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(auth_scheme),
    api_key: Optional[str] = Depends(api_key_scheme),
    auth_service: JWTAuthService = Depends(get_auth_service),
    api_key_service: APIKeyService = Depends(get_api_key_service),
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
            return auth_service.authenticate(credentials.credentials)
        else:
            return api_key_service.authenticate(api_key)
    except AuthError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from err
