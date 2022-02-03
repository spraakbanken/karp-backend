from typing import Dict, List

from fastapi import APIRouter, Body, Depends, HTTPException, Security
from starlette import status

from karp.foundation.commands import CommandBus
from karp import auth
from karp.auth.application.queries import GetResourcePermissions, ResourcePermissionDto

from karp.webapp.schemas import ResourceCreate, ResourcePublic
from karp.webapp.dependencies.auth import get_current_user, get_user
from karp.webapp.dependencies.fastapi_injector import inject_from_req




from karp.lex import ResourceUnitOfWork
from karp.lex.domain import commands
from karp.lex.application.queries import ReadOnlyResourceRepository



router = APIRouter()


@router.get(
    '/permissions',
    response_model=List[ResourcePermissionDto])
def list_resource_permissions(
    query: GetResourcePermissions = Depends(inject_from_req(GetResourcePermissions)),
):
    return query.query()


@router.get('/')
async def get_all_resources() -> List[Dict]:
    resources = [
        {'resource_id': 'places'},
    ]
    return resources


@router.post(
    '/',
    response_model=ResourcePublic,
    status_code=status.HTTP_201_CREATED
)
def create_new_resource(
    new_resource: ResourceCreate = Body(...),
    bus: CommandBus = Depends(inject_from_req(CommandBus)),
    user: auth.User = Security(get_user, scopes=["admin"]),
    resource_repo: ReadOnlyResourceRepository = Depends(inject_from_req(ReadOnlyResourceRepository)),
) -> ResourcePublic:
    try:
        if not new_resource.entry_repo_id:
            create_entry_repo = commands.CreateEntryRepository(
                repository_type='default',
                user=user.identifier,
                **new_resource.dict()
            )
            bus.dispatch(create_entry_repo)
            new_resource.entry_repo_id = create_entry_repo.entity_id
        create_resource = commands.CreateResource(
            created_by=user.identifier,
            **new_resource.dict(),
        )
        bus.dispatch(create_resource)
    except Exception as err:
        print(f'{err=}')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'{err=}',
        )
    resource = resource_repo.get_by_resource_id(create_resource.resource_id)
    return resource.dict()


@router.get(
    '/{resource_id}',
    response_model=ResourcePublic,
)
def get_resource_by_resource_id(
    resource_id: str,
    resource_repo: ReadOnlyResourceRepository = Depends(inject_from_req(ReadOnlyResourceRepository)),
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
