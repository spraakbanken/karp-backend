import logging  # noqa: I001

import injector
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session

from karp import lex
from karp.foundation.events import EventBus
from karp.lex.application.repositories import (
    ResourceUnitOfWork,
)
from karp.lex_infrastructure.queries import (
    SqlGetPublishedResources,
    SqlGetResources,
    GenericEntryViews,
    GenericGetEntryDiff,
    GenericGetEntryHistory,
    GenericGetHistory,
    SqlReadOnlyResourceRepository,
)
from karp.lex_infrastructure.repositories import (
    SqlResourceUnitOfWork,
)

logger = logging.getLogger(__name__)


class LexInfrastructure(injector.Module):  # noqa: D101
    @injector.provider
    def get_published_resources(  # noqa: D102
        self, conn: Connection
    ) -> SqlGetPublishedResources:
        return SqlGetPublishedResources(conn)

    @injector.provider
    def get_resources(self, conn: Connection) -> SqlGetResources:  # noqa: D102
        return SqlGetResources(conn)

    @injector.provider
    def read_only_resource_repo(  # noqa: D102
        self, conn: Connection
    ) -> SqlReadOnlyResourceRepository:
        return SqlReadOnlyResourceRepository(conn)

    @injector.provider
    def resource_uow(  # noqa: D102
        self,
        session: Session,
        event_bus: EventBus,
    ) -> ResourceUnitOfWork:
        return SqlResourceUnitOfWork(
            session=session,
            event_bus=event_bus,
        )

class GenericLexInfrastructure(injector.Module):  # noqa: D101
    @injector.provider
    def get_entry_diff(  # noqa: D102
        self,
        resource_uow: lex.ResourceUnitOfWork,
    ) -> GenericGetEntryDiff:
        return GenericGetEntryDiff(
            resource_uow=resource_uow,
        )

    @injector.provider
    def entry_views(  # noqa: D102
        self,
        resource_uow: ResourceUnitOfWork,
    ) -> GenericEntryViews:
        return GenericEntryViews(
            resource_uow=resource_uow,
        )

    @injector.provider
    def get_history(  # noqa: D102
        self,
        resource_uow: ResourceUnitOfWork,
    ) -> GenericGetHistory:
        return GenericGetHistory(
            resource_uow=resource_uow,
        )

    @injector.provider
    def get_entry_history(  # noqa: D102
        self,
        resource_uow: ResourceUnitOfWork,
    ) -> GenericGetEntryHistory:
        return GenericGetEntryHistory(
            resource_uow=resource_uow,
        )
