from fastapi import Depends
from karp.karp_v6_api.dependencies import db_deps
from karp.karp_v6_api.dependencies.db_deps import (
    get_session,
)
from karp.karp_v6_api.dependencies.fastapi_injector import inject_from_req
from karp.lex.application.repositories import ResourceRepository
from karp.lex_infrastructure import (
    GenericGetEntryDiff,
    GenericGetEntryHistory,
    GenericGetHistory,
    SqlGetPublishedResources,
    SqlReadOnlyResourceRepository,
    SqlResourceRepository,
)
from sqlalchemy.orm import Session
from starlette.requests import Request  # noqa: F401


def get_resource_repository(
    db_session: Session = Depends(get_session),
) -> ResourceRepository:
    return SqlResourceRepository(
        session=db_session,
    )


def get_resources_read_repo(  # noqa: D103
    resources: ResourceRepository = Depends(inject_from_req(ResourceRepository)),
) -> SqlReadOnlyResourceRepository:
    return SqlReadOnlyResourceRepository(resources)


def get_published_resources(  # noqa: D103
    session: Session = Depends(get_session),
) -> SqlGetPublishedResources:
    return SqlGetPublishedResources(session)


def get_entry_diff(  # noqa: D103
    resources: ResourceRepository = Depends(get_resource_repository),
) -> GenericGetEntryDiff:
    return GenericGetEntryDiff(
        resources=resources,
    )


def get_entry_history(  # noqa: D103
    resources: ResourceRepository = Depends(get_resource_repository),
) -> GenericGetEntryHistory:
    return GenericGetEntryHistory(
        resources=resources,
    )


def get_history(  # noqa: D103
    resources: ResourceRepository = Depends(get_resource_repository),
) -> GenericGetHistory:
    return GenericGetHistory(
        resources=resources,
    )
