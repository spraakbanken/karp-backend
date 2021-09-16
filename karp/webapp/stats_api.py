from dependency_injector import wiring
from fastapi import APIRouter, Security, HTTPException, status, Response, Depends

from karp.domain.models.user import User
from karp.domain.value_objects import PermissionLevel

from karp.services import entry_query
from karp.services.auth_service import AuthService
from karp.services.messagebus import MessageBus

# from karp.application import ctx

from karp.webapp import schemas
from .app_config import get_current_user
from .containers import WebAppContainer


router = APIRouter(tags=["Statistics"])


@router.get("/stats/{resource_id}/{field}")
@wiring.inject
def get_field_values(
    resource_id: str,
    field: str,
    user: User = Security(get_current_user, scopes=["read"]),
    auth_service: AuthService = Depends(wiring.Provide[WebAppContainer.auth_service]),
    bus: MessageBus = Depends(wiring.Provide[WebAppContainer.context.bus]),
):
    if not auth_service.authorize(PermissionLevel.read, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="read"'},
        )
    print("calling statistics ...")
    return entry_query.statistics(resource_id, field, bus.ctx)


def init_app(app):
    app.include_router(router)
