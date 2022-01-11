from typing import List

from fastapi import APIRouter, Depends

from karp.auth.application.queries import GetResourcePermissions, ResourcePermissionDto

from .fastapi_injector import inject_from_req
# from . import app_config
# from .containers import WebAppContainer

# from karp.infrastructure.unit_of_work import unit_of_work

# import karp.resourcemgr as resourcemgr


router = APIRouter(tags=["Resources"])


@router.get(
    "/resources",
    response_model=List[ResourcePermissionDto])
def list_resource_permissions(
    query: GetResourcePermissions = Depends(inject_from_req(GetResourcePermissions)),
):
    return query.query()


def init_app(app):
    app.include_router(router)
