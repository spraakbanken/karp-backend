import logging
import typing

import pydantic
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from karp import auth
from karp.api import dependencies as deps
from karp.api.dependencies.fastapi_injector import inject_from_req
from karp.auth.application import ResourcePermissionQueries
from karp.foundation.value_objects import PermissionLevel
from karp.lex.application import SearchQueries
from karp.lex.domain.errors import ResourceNotFound

logger = logging.getLogger(__name__)


router = APIRouter()


class StatisticsDto(pydantic.BaseModel):
    value: str | typing.Any
    count: int


@router.get(
    "/{resource_id}/{field}",
    response_model=typing.List[StatisticsDto],
    description="Return all possible values for `<field>` in `<resource_id>`",
)
def get_field_values(
    resource_id: str,
    field: str,
    user: auth.User = Depends(deps.get_user_optional),
    resource_permissions: ResourcePermissionQueries = Depends(deps.get_resource_permission_queries),
    search_queries: SearchQueries = Depends(inject_from_req(SearchQueries)),
    published_resources: typing.List[str] = Depends(deps.get_published_resources),
):
    if not resource_permissions.has_permission(PermissionLevel.read, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    if resource_id not in published_resources:
        raise ResourceNotFound(resource_id)
    logger.debug(f"calling statistics ... from {search_queries=}")
    return search_queries.statistics(resource_id, field)
