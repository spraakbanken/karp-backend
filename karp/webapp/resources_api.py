from fastapi import APIRouter

# from karp.application.services import resources

# from karp.infrastructure.unit_of_work import unit_of_work

# import karp.resourcemgr as resourcemgr

# conf_api = Blueprint("conf_api", __name__)

router = APIRouter()


@router.get("/resources")
def get_resources():
    result = []
    for resource in resources.get_published_resources():
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
