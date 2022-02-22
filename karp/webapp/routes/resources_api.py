import logging
from typing import Dict, List

from fastapi import APIRouter, Body, Depends, HTTPException, Security, status
import structlog

from karp.foundation.commands import CommandBus
from karp import auth, lex
from karp.auth.application.queries import GetResourcePermissions, ResourcePermissionDto

from karp.webapp.schemas import ResourceCreate, ResourcePublic
from karp.webapp import dependencies as deps, schemas
from karp.webapp.dependencies.fastapi_injector import inject_from_req

from karp.lex import (
    CreatingEntryRepo,
    CreatingResource,
    ResourceUnitOfWork,
    ResourceDto,
)
from karp.lex.domain import commands
from karp.lex.application.queries import ReadOnlyResourceRepository


router = APIRouter()
logger = structlog.get_logger()


@router.get(
    '/permissions',
    response_model=list[ResourcePermissionDto])
def list_resource_permissions(
    query: GetResourcePermissions = Depends(deps.get_resource_permissions),
):
    return query.query()


@router.get('/')
async def get_all_resources() -> list[dict]:
    resources = [
        {'resource_id': 'places'},
    ]
    return resources


@router.post(
    '/',
    response_model=ResourceDto,
    status_code=status.HTTP_201_CREATED
)
def create_new_resource(
    new_resource: ResourceCreate = Body(...),
    user: auth.User = Security(deps.get_user, scopes=["admin"]),
    auth_service: auth.AuthService = Depends(deps.get_auth_service),
    creating_resource_uc: CreatingResource = Depends(
        deps.get_lex_uc(CreatingResource)),
    creating_entry_repo_uc: CreatingEntryRepo = Depends(
        deps.get_lex_uc(CreatingEntryRepo)),
) -> ResourceDto:
    log = logger.bind()
    log.info('creating new resource', user=user.identifier,
             resource=new_resource)
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
            entry_repo = creating_entry_repo_uc.execute(
                commands.CreateEntryRepository(
                    repository_type='default',
                    user=user.identifier,
                    **new_resource.dict(),
                )
            )
            new_resource.entry_repo_id = entry_repo.entity_id
        create_resource = commands.CreateResource(
            user=user.identifier,
            **new_resource.dict(),
        )
        resource = creating_resource_uc.execute(create_resource)
        log.info('resource created', resource=resource)
        return resource
    except Exception as err:
        log.exception('error occured', user=user.identifier,
                      resource=new_resource)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'{err=}',
        )


@ router.post(
    '/{resource_id}/publish',
    # response_model=ResourceDto,
    status_code=status.HTTP_200_OK,
)
def publishing_resource(
    resource_id: str,
    resource_publish: schemas.ResourcePublish = Body(...),
    user: auth.User = Security(deps.get_user, scopes=["admin"]),
    auth_service: auth.AuthService = Depends(deps.get_auth_service),
    publishing_resource_uc: lex.PublishingResource = Depends(
        deps.get_lex_uc(lex.PublishingResource)),
):
    log = logger.bind()
    if not auth_service.authorize(
        auth.PermissionLevel.admin, user, [resource_id]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": 'Bearer scope="lexica:admin"'},
        )
    log.info('publishing resource',
             resource_id=resource_id, user=user.identifier)
    try:
        resource_publish.resource_id = resource_id
        publish_resource = commands.PublishResource(
            user=user.identifier,
            **resource_publish.dict(),
        )
        publishing_resource_uc.execute(publish_resource)
        logger.info("resource '%s' published", resource_id)
        return
    except Exception as err:
        log.exception('error occured when publishing',
                      resource_id=resource_id, user=user.identifier)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'{err=}',
        )


@ router.get(
    '/{resource_id}',
    response_model=ResourcePublic,
)
def get_resource_by_resource_id(
    resource_id: str,
    resource_repo: ReadOnlyResourceRepository = Depends(
        deps.get_resources_read_repo),
) -> ResourcePublic:
    resource = resource_repo.get_by_resource_id(resource_id)
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No resource with resource_id '{resource_id}' was found.",
        )
    return resource


def init_app(app):
    app.include_router(router)
