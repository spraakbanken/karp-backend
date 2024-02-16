import typing  # noqa: D100, I001
import logging

import pydantic
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,  # noqa: F401
    Security,
    status,
)

from karp import auth
from karp.auth_infrastructure import ResourcePermissionQueries
from karp.foundation.value_objects import PermissionLevel
from karp.search_infrastructure.queries import Es6SearchService
from karp.karp_v6_api import schemas  # noqa: F401

from karp.karp_v6_api import dependencies as deps
from karp.karp_v6_api.dependencies.fastapi_injector import inject_from_req

logger = logging.getLogger(__name__)


router = APIRouter()


class StatisticsDto(pydantic.BaseModel):  # noqa: D101
    value: str
    count: int


@router.get(
    "/{resource_id}/{field}",
    response_model=typing.List[StatisticsDto],
)
def get_field_values(  # noqa: ANN201, D103
    resource_id: str,
    field: str,
    user: auth.User = Security(deps.get_user_optional, scopes=["read"]),
    resource_permissions: ResourcePermissionQueries = Depends(deps.get_resource_permissions),
    search_service: Es6SearchService = Depends(inject_from_req(Es6SearchService)),
):
    if not resource_permissions.has_permission(PermissionLevel.read, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    logger.debug(f"calling statistics ... from {search_service=}")
    return search_service.statistics(resource_id, field)


def init_app(app):  # noqa: ANN201, D103
    app.include_router(router)
