from fastapi import APIRouter, Security, HTTPException, status, Response

from karp.domain.models.user import User
from karp.domain.value_objects import PermissionLevel

# from karp.application import ctx

from karp.webapp import schemas
from . import app_config


router = APIRouter()


@router.get("/{resource_id}/stats/{field}")
def get_field_values(
    resource_id: str,
    field: str,
    user: User = Security(app_config.get_current_user, scopes=["read"]),
):
    if not app_config.bus.ctx.auth_service.authorize(
        PermissionLevel.read, user, [resource_id], app_config.bus.ctx
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="read"'},
        )
    print("calling statistics ...")
    return app_config.bus.ctx.search_service.statistics(resource_id, field)


def init_app(app):
    app.include_router(router)
