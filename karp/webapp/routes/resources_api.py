import logging
from typing import Dict, List

from fastapi import APIRouter, Body, Depends, HTTPException, Security
from starlette import status

from karp.foundation.commands import CommandBus
from karp import auth
from karp.auth.application.queries import GetResourcePermissions, ResourcePermissionDto

from karp.webapp.schemas import ResourceCreate, ResourcePublic
from karp.webapp import dependencies as deps
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
logger = logging.getLogger(__name__)


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
    creating_resource_uc: CreatingResource = Depends(deps.get_lex_uc(CreatingResource)),
    creating_entry_repo_uc: CreatingEntryRepo = Depends(deps.get_lex_uc(CreatingEntryRepo)),
) -> ResourceDto:
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
        logger.info('resource created: %s', resource)
        return resource
    except Exception as err:
        print(f'{err=}')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'{err=}',
        )


@router.get(
    '/{resource_id}',
    response_model=ResourcePublic,
)
def get_resource_by_resource_id(
    resource_id: str,
    resource_repo: ReadOnlyResourceRepository = Depends(deps.get_resources_read_repo),
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
