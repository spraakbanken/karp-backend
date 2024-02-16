from fastapi import Depends
from sqlalchemy.orm import Session

from karp.api.dependencies.db_deps import (
    get_session,
)
from karp.api.dependencies.fastapi_injector import inject_from_req
from karp.lex_infrastructure import (
    EntryQueries,
    ResourceQueries,
    SqlResourceRepository,
)


def get_resource_repository(
    db_session: Session = Depends(get_session),
) -> SqlResourceRepository:
    return SqlResourceRepository(
        session=db_session,
    )


def get_resource_queries(
    resources: SqlResourceRepository = Depends(inject_from_req(SqlResourceRepository)),
) -> ResourceQueries:
    return ResourceQueries(resources)


def get_entry_queries(
    resources: SqlResourceRepository = Depends(inject_from_req(SqlResourceRepository)),
) -> EntryQueries:
    return EntryQueries(resources)
