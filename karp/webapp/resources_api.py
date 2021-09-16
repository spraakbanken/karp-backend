from dependency_injector import wiring
from fastapi import APIRouter, Depends

from karp.services import resource_views
from karp.services.messagebus import MessageBus

from . import app_config
from .containers import WebAppContainer

# from karp.infrastructure.unit_of_work import unit_of_work

# import karp.resourcemgr as resourcemgr


router = APIRouter(tags=["Resources"])


@router.get("/resources")
@wiring.inject
def list_resources(
    bus: MessageBus = Depends(wiring.Provide[WebAppContainer.context.bus]),
):
    result = []
    for resource in resource_views.get_published_resources(bus.ctx):
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
