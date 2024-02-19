from fastapi import Depends
from sqlalchemy.orm import Session

from karp.api.dependencies.db_deps import (
    get_session,
)
from karp.api.dependencies.fastapi_injector import inject_from_req
from karp.lex.application import (
    EntryQueries,
    ResourceQueries,
)
from karp.lex.infrastructure import ResourceRepository


def get_resource_repository(
    db_session: Session = Depends(get_session),
) -> ResourceRepository:
    return ResourceRepository(
        session=db_session,
    )


def get_resource_queries(
    resources: ResourceRepository = Depends(inject_from_req(ResourceRepository)),
) -> ResourceQueries:
    return ResourceQueries(resources)


def get_entry_queries(
    resources: ResourceRepository = Depends(inject_from_req(ResourceRepository)),
) -> EntryQueries:
    return EntryQueries(resources)
