# from dependency_injector import wiring
from fastapi import APIRouter, Depends

from karp.auth.application.queries import GetResourcePermissions
from karp.services.messagebus import MessageBus

from .fastapi_injector import inject_from_req
# from . import app_config
# from .containers import WebAppContainer

# from karp.infrastructure.unit_of_work import unit_of_work

# import karp.resourcemgr as resourcemgr


router = APIRouter(tags=["Resources"])


@router.get("/resources")
def list_resource_permissions(
    query: GetResourcePermissions = Depends(inject_from_req(GetResourcePermissions)),
):
    result = []
    for resource in query.query():
        resource_obj = {"resource_id": resource.resource_id}

        protected_conf = resource.config.get("protected")
        if not protected_conf:
            protected = None
        elif protected_conf.get("admin"):
            protected = "ADMIN"
        elif protected_conf.get("write"):
            protected = "WRITE"
        else:
            protected = "READ"

        if protected:
            resource_obj["protected"] = protected
        result.append(resource_obj)

    return result


def init_app(app):
    app.include_router(router)
