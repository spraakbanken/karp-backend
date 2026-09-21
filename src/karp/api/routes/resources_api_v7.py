import logging
import typing

from fastapi import APIRouter

from karp.api.schemas import ResourceProtected, ResourcePublic
from karp.auth.application.resources import ResourcePermissionDto
from karp.lex.application import resource_queries
from karp.lex.domain.dtos import ResourceDto
from karp.lex.infrastructure.sql import resource_repository

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/permissions", response_model=list[ResourcePermissionDto])
def list_resource_permissions():
    resource_permissions = []
    for resource in resource_repository.get_published_resources():
        protected_conf = resource.config.protected
        if not protected_conf:
            protected = None
        elif protected_conf.get("admin"):
            protected = "ADMIN"
        elif protected_conf.get("write"):
            protected = "WRITE"
        else:
            protected = "READ"
        resource_permissions.append(ResourcePermissionDto(resource_id=resource.resource_id, protected=protected))

    return resource_permissions


@router.get(
    "/",
    response_model=list[ResourceProtected],
)
def get_all_resources() -> typing.List[ResourceDto]:
    return list(resource_queries.get_all_resources())


@router.get(
    "/{resource_id}",
    response_model=ResourcePublic,
)
def get_resource_by_resource_id(
    resource_id: str,
) -> ResourcePublic:
    return resource_queries.by_resource_id(resource_id)
