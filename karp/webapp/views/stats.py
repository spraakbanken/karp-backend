from fastapi import APIRouter, Security, HTTPException, status, Response

from karp.domain.models.user import User
from karp.domain.models.auth_service import PermissionLevel

from karp.application import ctx

from karp.webapp import schemas
from karp.webapp.auth import get_current_user


router = APIRouter()


@router.get("/{resource_id}/stats/{field}")
def get_field_values(
    resource_id: str,
    field: str,
    user: User = Security(get_current_user, scopes=["read"]),
):
    if not ctx.auth_service.authorize(PermissionLevel.read, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="read"'},
        )
    print("calling statistics ...")
    return ctx.search_service.statistics(resource_id, field)


def init_app(app):
    app.include_router(router)
