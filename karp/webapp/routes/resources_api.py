from typing import List

from fastapi import APIRouter, Depends

from karp.auth.application.queries import GetResourcePermissions, ResourcePermissionDto

from karp.webapp.dependencies.fastapi_injector import inject_from_req


router = APIRouter()


@router.get(
    '/',
    response_model=List[ResourcePermissionDto])
def list_resource_permissions(
    query: GetResourcePermissions = Depends(inject_from_req(GetResourcePermissions)),
):
    return query.query()


def init_app(app):
    app.include_router(router)
