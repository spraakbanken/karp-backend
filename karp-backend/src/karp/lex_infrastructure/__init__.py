import logging  # noqa: I001

import injector
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session

from karp import lex
from karp.foundation.events import EventBus
from karp.lex.application.repositories import (
    EntryUowRepositoryUnitOfWork,
    ResourceUnitOfWork,
)
from karp.lex_infrastructure.queries import (
    SqlGetPublishedResources,
    SqlGetResources,
    SqlListEntryRepos,
    GenericEntryViews,
    GenericGetEntryDiff,
    GenericGetEntryHistory,
    GenericGetHistory,
    SqlReadOnlyEntryRepoRepository,
    SqlReadOnlyResourceRepository,
)
from karp.lex_infrastructure.repositories import (
    SqlEntryUowRepositoryUnitOfWork,
    SqlResourceUnitOfWork,
)
from karp.lex_infrastructure.queries.generic_resources import GenericGetEntryRepositoryId

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
    def list_entry_repos(self, conn: Connection) -> SqlListEntryRepos:  # noqa: D102
        return SqlListEntryRepos(conn)

    @injector.provider
    def read_only_entry_repo_repo(  # noqa: D102
        self, conn: Connection
    ) -> SqlReadOnlyEntryRepoRepository:
        return SqlReadOnlyEntryRepoRepository(conn)

    @injector.provider
    # @injector.singleton
    def entry_uow_repo(  # noqa: D102
        self,
        session: Session,
        event_bus: EventBus,
    ) -> EntryUowRepositoryUnitOfWork:
        logger.debug("creating entry_repo_uow", extra={"session": session})
        return SqlEntryUowRepositoryUnitOfWork(
            session=session,
            event_bus=event_bus,
        )

    @injector.provider
    def resources_uow(  # noqa: D102
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
    def gey_entry_diff(  # noqa: D102
        self,
        resources_uow: lex.ResourceUnitOfWork,
        entry_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> GenericGetEntryDiff:
        return GenericGetEntryDiff(
            resource_uow=resources_uow,
            entry_repo_uow=entry_repo_uow,
        )

    @injector.provider
    def get_entry_repo_id(  # noqa: D102
        self,
        resources_uow: ResourceUnitOfWork,
    ) -> GenericGetEntryRepositoryId:
        return GenericGetEntryRepositoryId(
            resource_uow=resources_uow,
        )

    @injector.provider
    def entry_views(  # noqa: D102
        self,
        get_entry_repo_id: GenericGetEntryRepositoryId,
        entry_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> GenericEntryViews:
        return GenericEntryViews(
            get_entry_repo_id=get_entry_repo_id,
            entry_repo_uow=entry_repo_uow,
        )

    @injector.provider
    def get_history(  # noqa: D102
        self,
        resources_uow: ResourceUnitOfWork,
        entry_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> GenericGetHistory:
        return GenericGetHistory(
            resource_uow=resources_uow,
            entry_repo_uow=entry_repo_uow,
        )

    @injector.provider
    def get_entry_history(  # noqa: D102
        self,
        resources_uow: ResourceUnitOfWork,
        entry_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> GenericGetEntryHistory:
        return GenericGetEntryHistory(
            resource_uow=resources_uow,
            entry_repo_uow=entry_repo_uow,
        )
