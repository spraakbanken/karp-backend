from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, SecurityScopes

from karp import bootstrap

# from karp.auth.auth import auth
from karp.errors import ClientErrorCodes, KarpError


bus = bootstrap.bootstrap()


auth_scheme = HTTPBearer()


def get_current_user(
    security_scopes: SecurityScopes,
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
):
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
        print("webapp.app_config.get_current_user: Calling auth_service")
        user = bus.ctx.auth_service.authenticate(
            credentials.scheme, credentials.credentials
        )
        if user is None:
            raise credentials_exception
        return user
    except KarpError:
        raise credentials_exception
