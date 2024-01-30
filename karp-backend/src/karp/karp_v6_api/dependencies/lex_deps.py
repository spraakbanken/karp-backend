from typing import Callable, Type  # noqa: D100, I001
from fastapi import Depends
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session
from starlette.requests import Request  # noqa: F401

from karp.foundation.events import EventBus
from karp.lex import (
    EntryUowRepositoryUnitOfWork,
    ResourceUnitOfWork,
)
from karp.karp_v6_api.dependencies import db_deps
from karp.karp_v6_api.dependencies.db_deps import (
    get_database,  # noqa: F401
    get_session,
)
from karp.karp_v6_api.dependencies import event_deps
from karp.karp_v6_api.dependencies.fastapi_injector import inject_from_req

from karp.db_infrastructure import Database  # noqa: F401

from karp.lex_infrastructure import (
    GenericGetEntryDiff,
    GenericGetEntryHistory,
    GenericGetHistory,
    SqlEntryUowRepositoryUnitOfWork,
    SqlGetPublishedResources,
    SqlResourceUnitOfWork,
    SqlReadOnlyResourceRepository,
)


def get_resource_unit_of_work(  # noqa: D103
    db_session: Session = Depends(get_session),
    event_bus: EventBus = Depends(event_deps.get_eventbus),
) -> ResourceUnitOfWork:
    return SqlResourceUnitOfWork(
        event_bus=event_bus,
        session=db_session,
    )


def get_entry_repo_uow(  # noqa: D103
    db_session: Session = Depends(get_session),
    event_bus: EventBus = Depends(event_deps.get_eventbus),
) -> EntryUowRepositoryUnitOfWork:
    return SqlEntryUowRepositoryUnitOfWork(
        event_bus=event_bus,
        session=db_session,
    )


def get_resources_read_repo(  # noqa: D103
    conn: Connection = Depends(db_deps.get_connection),
) -> SqlReadOnlyResourceRepository:
    return SqlReadOnlyResourceRepository(conn)


def get_published_resources(  # noqa: D103
    conn: Connection = Depends(db_deps.get_connection),
) -> SqlGetPublishedResources:
    return SqlGetPublishedResources(conn)


def get_entry_diff(  # noqa: D103
    resource_uow: ResourceUnitOfWork = Depends(get_resource_unit_of_work),
    entry_repo_uow: EntryUowRepositoryUnitOfWork = Depends(get_entry_repo_uow),
) -> GenericGetEntryDiff:
    return GenericGetEntryDiff(
        resource_uow=resource_uow,
        entry_repo_uow=entry_repo_uow,
    )


def get_entry_history(  # noqa: D103
    resource_uow: ResourceUnitOfWork = Depends(get_resource_unit_of_work),
    entry_repo_uow: EntryUowRepositoryUnitOfWork = Depends(get_entry_repo_uow),
) -> GenericGetEntryHistory:
    return GenericGetEntryHistory(
        resource_uow=resource_uow,
        entry_repo_uow=entry_repo_uow,
    )


def get_history(  # noqa: D103
    resource_uow: ResourceUnitOfWork = Depends(get_resource_unit_of_work),
    entry_repo_uow: EntryUowRepositoryUnitOfWork = Depends(get_entry_repo_uow),
) -> GenericGetHistory:
    return GenericGetHistory(
        resource_uow=resource_uow,
        entry_repo_uow=entry_repo_uow,
    )
