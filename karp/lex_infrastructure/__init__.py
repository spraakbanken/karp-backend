from typing import Dict
import injector
from sqlalchemy.engine import Connection
from sqlalchemy.orm import sessionmaker

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
    SqlReadOnlyResourceRepository,)
from karp.lex_infrastructure.repositories import (
    SqlEntryUowRepositoryUnitOfWork,
    SqlEntryUowCreator,
    SqlResourceUnitOfWork,
)


class LexInfrastructure(injector.Module):
    @injector.provider
    def get_published_resources(self, conn: Connection) -> GetPublishedResources:
        return SqlGetPublishedResources(conn)

    @injector.provider
    def get_resources(self, conn: Connection) -> GetResources:
        return SqlGetResources(conn)

    @injector.provider
    def read_only_resource_repo(self, conn: Connection) -> ReadOnlyResourceRepository:
        return SqlReadOnlyResourceRepository(conn)

    @injector.provider
    def list_entry_repos(self, conn: Connection) -> ListEntryRepos:
        return SqlListEntryRepos(conn)

    @injector.provider
    @injector.singleton
    def entry_uow_repo(
        self,
        session_factory: sessionmaker,
        entry_uow_factory: EntryRepositoryUnitOfWorkFactory,
        event_bus: EventBus,
    ) -> EntryUowRepositoryUnitOfWork:
        return SqlEntryUowRepositoryUnitOfWork(
            session_factory=session_factory,
            entry_uow_factory=entry_uow_factory,
            event_bus=event_bus,
        )

    @injector.provider
    def resources_uow(
        self,
        session_factory: sessionmaker,
        event_bus: EventBus,
    ) -> ResourceUnitOfWork:
        return SqlResourceUnitOfWork(
            session_factory=session_factory,
            event_bus=event_bus,
        )

    @injector.multiprovider
    def entry_uow_creator_map(self) -> Dict[str, EntryUnitOfWorkCreator]:
        return {
            'default': SqlEntryUowCreator,
            SqlEntryUowCreator.repository_type: SqlEntryUowCreator,
        }


class GenericLexInfrastructure(injector.Module):
    @injector.provider
    def get_referenced_entries(
        self,
        resources_repo: ReadOnlyResourceRepository,
        entry_uow_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> GetReferencedEntries:
        return GenericGetReferencedEntries(
            resource_repo=resources_repo,
            entry_uow_repo_uow=entry_uow_repo_uow,
        )

    @injector.provider
    def gey_entry_diff(
        self,
        resources_uow: ResourceUnitOfWork,
        entry_uow_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> GetEntryDiff:
        return GenericGetEntryDiff(
            resource_uow=resources_uow,
            entry_uow_repo_uow=entry_uow_repo_uow,
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
        entry_uow_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> EntryViews:
        return GenericEntryViews(
            get_entry_repo_id=get_entry_repo_id,
            entry_uow_repo_uow=entry_uow_repo_uow,
        )

    @injector.provider
    def get_history(
        self,
        resources_uow: ResourceUnitOfWork,
        entry_uow_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> GetHistory:
        return GenericGetHistory(
            resource_uow=resources_uow,
            entry_uow_repo_uow=entry_uow_repo_uow,
        )

    @injector.provider
    def get_entry_history(
        self,
        resources_uow: ResourceUnitOfWork,
        entry_uow_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> GetEntryHistory:
        return GenericGetEntryHistory(
            resource_uow=resources_uow,
            entry_uow_repo_uow=entry_uow_repo_uow,
        )
