from fastapi import APIRouter

from karp.services import resource_views

from . import app_config

# from karp.infrastructure.unit_of_work import unit_of_work

# import karp.resourcemgr as resourcemgr


router = APIRouter()


@router.get("/resources")
def list_resources():
    result = []
    for resource in resource_views.get_published_resources(app_config.bus.ctx):
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
