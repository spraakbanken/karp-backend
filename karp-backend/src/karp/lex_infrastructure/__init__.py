import logging  # noqa: I001

import injector
from sqlalchemy.orm import Session

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
    SqlResourceRepository,
)
from karp.lex.application.repositories import ResourceRepository

logger = logging.getLogger(__name__)


class LexInfrastructure(injector.Module):  # noqa: D101
    @injector.provider
    def get_published_resources(  # noqa: D102
        self, session: Session
    ) -> SqlGetPublishedResources:
        return SqlGetPublishedResources(session)

    @injector.provider
    def get_resources(self, session: Session) -> SqlGetResources:  # noqa: D102
        return SqlGetResources(session)

    @injector.provider
    def read_only_resource_repo(  # noqa: D102
        self, resources: ResourceRepository
    ) -> SqlReadOnlyResourceRepository:
        return SqlReadOnlyResourceRepository(resources)

    @injector.provider
    def resources(  # noqa: D102
        self,
        session: Session,
    ) -> ResourceRepository:
        return SqlResourceRepository(
            session=session,
        )


class GenericLexInfrastructure(injector.Module):  # noqa: D101
    @injector.provider
    def get_entry_diff(  # noqa: D102
        self,
        resources: ResourceRepository,
    ) -> GenericGetEntryDiff:
        return GenericGetEntryDiff(
            resources=resources,
        )

    @injector.provider
    def entry_views(  # noqa: D102
        self,
        resources: ResourceRepository,
    ) -> GenericEntryViews:
        return GenericEntryViews(
            resources=resources,
        )

    @injector.provider
    def get_history(  # noqa: D102
        self,
        resources: ResourceRepository,
    ) -> GenericGetHistory:
        return GenericGetHistory(
            resources=resources,
        )

    @injector.provider
    def get_entry_history(  # noqa: D102
        self,
        resources: ResourceRepository,
    ) -> GenericGetEntryHistory:
        return GenericGetEntryHistory(
            resources=resources,
        )
