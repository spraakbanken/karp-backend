import logging
import typing

from fastapi import APIRouter

from karp.api.schemas import ResourceProtected, ResourcePublic
from karp.auth.application import resource_permission_queries as resource_permissions
from karp.auth.application.resources import ResourcePermissionDto
from karp.lex.application import resource_queries
from karp.lex.domain.dtos import ResourceDto

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/permissions", response_model=list[ResourcePermissionDto])
def list_resource_permissions():
    return resource_permissions.get_resource_permissions()


@router.get(
    "/",
    response_model=list[ResourceProtected],
)
def get_all_resources() -> typing.List[ResourceDto]:
    return list(resource_queries.get_all_resources())


@router.get(
    "/{resource_id}",
    response_model=ResourcePublic,
)
def get_resource_by_resource_id(
    resource_id: str,
) -> ResourcePublic:
    return resource_queries.by_resource_id(resource_id)
