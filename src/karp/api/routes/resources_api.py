import logging
import typing

from fastapi import APIRouter, Depends

from karp.api import dependencies as deps
from karp.api.dependencies.fastapi_injector import inject_from_req
from karp.api.schemas import ResourceProtected, ResourcePublic
from karp.auth.application import ResourcePermissionQueries
from karp.auth.application.resources import ResourcePermissionDto
from karp.lex.application import ResourceQueries
from karp.lex.domain.dtos import ResourceDto

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/permissions", response_model=list[ResourcePermissionDto])
def list_resource_permissions(
    resource_permissions: ResourcePermissionQueries = Depends(deps.get_resource_permission_queries),
):
    return resource_permissions.get_resource_permissions()


@router.get(
    "/",
    response_model=list[ResourceProtected],
)
def get_all_resources(
    resources: ResourceQueries = Depends(inject_from_req(ResourceQueries)),
) -> typing.List[ResourceDto]:
    return list(resources.get_all_resources())


@router.get(
    "/{resource_id}",
    response_model=ResourcePublic,
)
def get_resource_by_resource_id(
    resource_id: str,
    resource_queries: ResourceQueries = Depends(deps.get_resource_queries),
) -> ResourcePublic:
    return resource_queries.by_resource_id(resource_id)
