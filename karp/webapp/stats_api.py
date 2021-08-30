from fastapi import APIRouter, Security, HTTPException, status, Response

from karp.domain.models.user import User
from karp.domain.value_objects import PermissionLevel

from karp.services import entry_query

# from karp.application import ctx

from karp.webapp import schemas
from .app_config import bus, get_current_user


router = APIRouter()


@router.get("/stats/{resource_id}/{field}")
def get_field_values(
    resource_id: str,
    field: str,
    user: User = Security(get_current_user, scopes=["read"]),
):
    if not bus.ctx.auth_service.authorize(
        PermissionLevel.read, user, [resource_id], bus.ctx
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="read"'},
        )
    print("calling statistics ...")
    return entry_query.statistics(resource_id, field, bus.ctx)


def init_app(app):
    app.include_router(router)
