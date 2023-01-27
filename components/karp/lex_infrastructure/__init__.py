import logging
from typing import Dict

import injector
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session

from karp import lex
from karp.foundation.events import EventBus
from karp.lex.application.queries import (
    GetPublishedResources,
    GetResources,
    ResourceDto,
    ListEntryRepos,
    EntryRepoDto,
    GetReferencedEntries,
    GetEntryRepositoryId,
    EntryViews,
    GetEntryDiff,
    GetEntryHistory,
    GetHistory,
)
from karp.lex.application.queries.resources import ReadOnlyResourceRepository
from karp.lex.application.repositories import (
    EntryUowRepositoryUnitOfWork,
    EntryRepositoryUnitOfWorkFactory,
    EntryUnitOfWorkCreator,
    ResourceUnitOfWork,
)
from karp.lex_infrastructure.queries import (
    SqlGetPublishedResources,
    SqlGetResources,
    SqlListEntryRepos,
    GenericGetReferencedEntries,
    GenericGetEntryRepositoryId,
    GenericEntryViews,
    GenericGetEntryDiff,
    GenericEntryQuery,
    GenericGetEntryHistory,
    GenericGetHistory,
    SqlReadOnlyEntryRepoRepositry,
    SqlReadOnlyResourceRepository,
)
from karp.lex_infrastructure.repositories import (
    SqlEntryUowRepositoryUnitOfWork,
    SqlEntryUowV1Creator,
    SqlEntryUowV2Creator,
    SqlResourceUnitOfWork,
)


logger = logging.getLogger(__name__)


class LexInfrastructure(injector.Module):
    @injector.provider
    def get_published_resources(self, conn: Connection) -> lex.GetPublishedResources:
        return SqlGetPublishedResources(conn)

    @injector.provider
    def get_resources(self, conn: Connection) -> lex.GetResources:
        return SqlGetResources(conn)

    @injector.provider
    def read_only_resource_repo(
        self, conn: Connection
    ) -> lex.ReadOnlyResourceRepository:
        return SqlReadOnlyResourceRepository(conn)

    @injector.provider
    def list_entry_repos(self, conn: Connection) -> lex.ListEntryRepos:
        return SqlListEntryRepos(conn)

    @injector.provider
    def read_only_entry_repo_repo(
        self, conn: Connection
    ) -> lex.ReadOnlyEntryRepoRepositry:
        return SqlReadOnlyEntryRepoRepositry(conn)

    @injector.provider
    # @injector.singleton
    def entry_uow_repo(
        self,
        session: Session,
        entry_uow_factory: EntryRepositoryUnitOfWorkFactory,
        event_bus: EventBus,
    ) -> EntryUowRepositoryUnitOfWork:
        logger.debug("creating entry_repo_uow", extra={"session": session})
        return SqlEntryUowRepositoryUnitOfWork(
            session=session,
            entry_uow_factory=entry_uow_factory,
            event_bus=event_bus,
        )

    @injector.provider
    def resources_uow(
        self,
        session: Session,
        event_bus: EventBus,
    ) -> ResourceUnitOfWork:
        return SqlResourceUnitOfWork(
            session=session,
            event_bus=event_bus,
        )

    @injector.multiprovider
    def entry_uow_creator_map(self) -> Dict[str, EntryUnitOfWorkCreator]:
        return {
            "default": SqlEntryUowV2Creator,
            SqlEntryUowV1Creator.repository_type: SqlEntryUowV1Creator,
            SqlEntryUowV2Creator.repository_type: SqlEntryUowV2Creator,
        }


class GenericLexInfrastructure(injector.Module):
    @injector.provider
    def get_referenced_entries(
        self,
        resources_repo: ReadOnlyResourceRepository,
        entry_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> GetReferencedEntries:
        return GenericGetReferencedEntries(
            resource_repo=resources_repo,
            entry_repo_uow=entry_repo_uow,
        )

    @injector.provider
    def gey_entry_diff(
        self,
        resources_uow: lex.ResourceUnitOfWork,
        entry_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> GetEntryDiff:
        return GenericGetEntryDiff(
            resource_uow=resources_uow,
            entry_repo_uow=entry_repo_uow,
        )

    @injector.provider
    def get_entry_repo_id(
        self,
        resources_uow: ResourceUnitOfWork,
    ) -> GetEntryRepositoryId:
        return GenericGetEntryRepositoryId(
            resource_uow=resources_uow,
        )

    @injector.provider
    def entry_views(
        self,
        get_entry_repo_id: GetEntryRepositoryId,
        entry_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> EntryViews:
        return GenericEntryViews(
            get_entry_repo_id=get_entry_repo_id,
            entry_repo_uow=entry_repo_uow,
        )

    @injector.provider
    def get_history(
        self,
        resources_uow: ResourceUnitOfWork,
        entry_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> GetHistory:
        return GenericGetHistory(
            resource_uow=resources_uow,
            entry_repo_uow=entry_repo_uow,
        )

    @injector.provider
    def get_entry_history(
        self,
        resources_uow: ResourceUnitOfWork,
        entry_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> GetEntryHistory:
        return GenericGetEntryHistory(
            resource_uow=resources_uow,
            entry_repo_uow=entry_repo_uow,
        )
