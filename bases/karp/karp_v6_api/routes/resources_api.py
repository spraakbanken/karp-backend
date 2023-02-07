import logging
import typing

from fastapi import APIRouter, Body, Depends, HTTPException, Security, status

from karp import auth, lex
from karp.auth.application.queries import GetResourcePermissions, ResourcePermissionDto

from karp.karp_v6_api.schemas import ResourceCreate, ResourcePublic, ResourceProtected
from karp.karp_v6_api import dependencies as deps, schemas

from karp.command_bus import CommandBus
from karp.lex import ResourceDto

from karp.lex_core import commands
from karp.lex.application.queries import ReadOnlyResourceRepository


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/permissions", response_model=list[ResourcePermissionDto])
def list_resource_permissions(
    query: GetResourcePermissions = Depends(deps.get_resource_permissions),
):
    return query.query()


@router.get(
    "/",
    response_model=list[ResourceProtected],
)
def get_all_resources(
    get_resources: lex.GetResources = Depends(deps.inject_from_req(lex.GetResources)),
) -> typing.Iterable[lex.ResourceDto]:
    return get_resources.query()


@router.post("/", response_model=ResourceDto, status_code=status.HTTP_201_CREATED)
def create_new_resource(
    new_resource: ResourceCreate = Body(...),
    user: auth.User = Security(deps.get_user, scopes=["admin"]),
    auth_service: auth.AuthService = Depends(deps.get_auth_service),
    command_bus: CommandBus = Depends(deps.inject_from_req(CommandBus)),
) -> ResourceDto:
    logger.info(
        "creating new resource",
        extra={"user": user.identifier, "resource": new_resource},
    )
    if not auth_service.authorize(
        auth.PermissionLevel.admin, user, [new_resource.resource_id]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="lexica:admin"'},
        )
    try:
        if new_resource.entry_repo_id is None:
            entry_repo = command_bus.dispatch(
                commands.CreateEntryRepository(
                    repository_type="default",
                    name=new_resource.resource_id,
                    config=new_resource.config,
                    user=user.identifier,
                    message=new_resource.message or "Entry repository created",
                )
            )
            new_resource.entry_repo_id = entry_repo.entity_id
        create_resource = commands.CreateResource(
            user=user.identifier,
            **new_resource.dict(),
        )
        resource = command_bus.dispatch(create_resource)
        logger.info("resource created", extra={"resource": resource})
        return resource
    except Exception as err:
        logger.exception(
            "error occured", extra={"user": user.identifier, "resource": new_resource}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{err=}",
        ) from err


@router.post(
    "/{resource_id}/publish",
    # response_model=ResourceDto,
    status_code=status.HTTP_200_OK,
)
def publishing_resource(
    resource_id: str,
    resource_publish: schemas.ResourcePublish = Body(...),
    user: auth.User = Security(deps.get_user, scopes=["admin"]),
    auth_service: auth.AuthService = Depends(deps.get_auth_service),
    command_bus: CommandBus = Depends(deps.inject_from_req(CommandBus)),
):
    if not auth_service.authorize(auth.PermissionLevel.admin, user, [resource_id]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="lexica:admin"'},
        )
    logger.info(
        "publishing resource",
        extra={"resource_id": resource_id, "user": user.identifier},
    )
    try:
        resource_publish.resource_id = resource_id
        publish_resource = commands.PublishResource(
            user=user.identifier,
            **resource_publish.dict(),
        )
        command_bus.dispatch(publish_resource)
        logger.info("resource published", extra={"resource_id": resource_id})
        return
    except Exception as err:
        logger.exception(
            "error occured when publishing",
            extra={"resource_id": resource_id, "user": user.identifier},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{err=}",
        ) from err


@router.get(
    "/{resource_id}",
    response_model=ResourcePublic,
)
def get_resource_by_resource_id(
    resource_id: str,
    resource_repo: ReadOnlyResourceRepository = Depends(deps.get_resources_read_repo),
) -> ResourcePublic:
    if resource := resource_repo.get_by_resource_id(resource_id):
        return ResourcePublic(**resource.dict())
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No resource with resource_id '{resource_id}' was found.",
        )


def init_app(app):
    app.include_router(router)
