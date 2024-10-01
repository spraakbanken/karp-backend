from typing import List

from fastapi import Depends
from sqlalchemy.orm import Session

from karp.api.dependencies.db_deps import (
    get_session,
)
from karp.api.dependencies.fastapi_injector import inject_from_req
from karp.auth.infrastructure import APIKeyService
from karp.lex.application import (
    EntryQueries,
    ResourceQueries,
)
from karp.lex.infrastructure import ResourceRepository
from karp.plugins import Plugins


def get_api_key_service(
    db_session: Session = Depends(get_session),
) -> APIKeyService:
    return APIKeyService(session=db_session)


def get_resource_repository(
    db_session: Session = Depends(get_session),
) -> ResourceRepository:
    return ResourceRepository(
        session=db_session,
    )


def get_resource_queries(
    resources: ResourceRepository = Depends(inject_from_req(ResourceRepository)),
    plugins: Plugins = Depends(inject_from_req(Plugins)),
) -> ResourceQueries:
    return ResourceQueries(resources, plugins)


def get_entry_queries(
    resources: ResourceRepository = Depends(inject_from_req(ResourceRepository)),
    plugins: Plugins = Depends(inject_from_req(Plugins)),
) -> EntryQueries:
    return EntryQueries(resources, plugins)


# TODO This should be cached
def get_published_resources(
    resources: ResourceRepository = Depends(inject_from_req(ResourceRepository)),
) -> List[str]:
    return [resource.resource_id for resource in resources.get_published_resources()]
