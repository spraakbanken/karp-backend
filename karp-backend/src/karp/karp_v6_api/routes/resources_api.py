import logging  # noqa: D100, I001
import typing

from fastapi import APIRouter, Depends, HTTPException, status

from karp.auth.application.queries.resources import ResourcePermissionDto
from karp.auth_infrastructure import LexGetResourcePermissions
from karp.karp_v6_api.schemas import ResourcePublic, ResourceProtected
from karp.karp_v6_api import dependencies as deps
from karp.karp_v6_api.dependencies.fastapi_injector import inject_from_req
from karp.lex.application.dtos import ResourceDto
from karp.lex_infrastructure import SqlGetResources, SqlReadOnlyResourceRepository

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/permissions", response_model=list[ResourcePermissionDto])
def list_resource_permissions(  # noqa: ANN201, D103
    query: LexGetResourcePermissions = Depends(deps.get_resource_permissions),
):
    return query.query()


@router.get(
    "/",
    response_model=list[ResourceProtected],
)
def get_all_resources(  # noqa: D103
    get_resources: SqlGetResources = Depends(inject_from_req(SqlGetResources)),
) -> typing.Iterable[ResourceDto]:
    return get_resources.query()


@router.get(
    "/{resource_id}",
    response_model=ResourcePublic,
)
def get_resource_by_resource_id(  # noqa: D103
    resource_id: str,
    resource_repo: SqlReadOnlyResourceRepository = Depends(deps.get_resources_read_repo),
) -> ResourcePublic:
    if resource := resource_repo.get_by_resource_id(resource_id):
        return resource  # type: ignore [return-value]
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No resource with resource_id '{resource_id}' was found.",
        )


def init_app(app):  # noqa: ANN201, D103
    app.include_router(router)
