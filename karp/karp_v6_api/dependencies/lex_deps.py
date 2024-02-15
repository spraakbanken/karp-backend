from fastapi import Depends
from karp.karp_v6_api.dependencies import db_deps
from karp.karp_v6_api.dependencies.db_deps import (
    get_session,
)
from karp.karp_v6_api.dependencies.fastapi_injector import inject_from_req
from karp.lex.application.repositories import ResourceRepository
from karp.lex_infrastructure import (
    EntryQueries,
    ResourceQueries,
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


def get_resource_queries(  # noqa: D103
    resources: ResourceRepository = Depends(inject_from_req(ResourceRepository)),
) -> ResourceQueries:
    return ResourceQueries(resources)


def get_entry_queries(  # noqa: D103
    resources: ResourceRepository = Depends(inject_from_req(ResourceRepository)),
) -> EntryQueries:
    return EntryQueries(resources)
