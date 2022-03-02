import injector

from karp.foundation.commands import CommandHandler
from karp.lex.application.repositories import (
    EntryUowRepositoryUnitOfWork,
    EntryRepositoryUnitOfWorkFactory,
    InjectorEntryUnitOfWorkRepoFactory,
    ResourceUnitOfWork,
)
from karp.lex.domain.commands import (
    CreateEntryRepository,
    CreateResource,
)
from karp.lex.domain import commands
from karp.lex.domain.value_objects import EntrySchema
from karp.lex.application.use_cases import (
    AddingEntries,
    AddingEntry,
    CreatingEntryRepo,
    CreatingResource,
    DeletingEntry,
    PublishingResource,
    UpdatingEntry,
    UpdatingResource,
)
from karp.lex.application.queries import (
    EntryDto,
    GetEntryDiff,
    GetEntryHistory,
    GetHistory,
    GetHistoryDto,
    GetPublishedResources,
    GetResources,
    HistoryDto,
    ResourceDto,
    ReadOnlyResourceRepository,
    EntryRepoDto,
    ReadOnlyEntryRepoRepositry,
    ListEntryRepos,
)


class Lex(injector.Module):
    @injector.provider
    def entry_uow_factory(self, container: injector.Injector) -> EntryRepositoryUnitOfWorkFactory:
        return InjectorEntryUnitOfWorkRepoFactory(container)

    @injector.provider
    def create_entry_repository(
        self,
        uow: EntryUowRepositoryUnitOfWork,
    ) -> CommandHandler[CreateEntryRepository]:
        return CreatingEntryRepo(
            entry_repo_uow=uow,
        )

    @injector.provider
    def create_resource(
        self,
        entry_repo_uow: EntryUowRepositoryUnitOfWork,
        resource_uow: ResourceUnitOfWork,
    ) -> CommandHandler[CreateResource]:
        return CreatingResource(
            entry_repo_uow=entry_repo_uow,
            resource_uow=resource_uow,
        )

    @injector.provider
    def update_resource(
        self,
        resource_uow: ResourceUnitOfWork,
    ) -> CommandHandler[commands.UpdateResource]:
        return UpdatingResource(resource_uow)

    @injector.provider
    def publish_resource(
        self,
        resource_uow: ResourceUnitOfWork,
    ) -> CommandHandler[commands.PublishResource]:
        return PublishingResource(resource_uow)

    @injector.provider
    def add_entry(
        self,
        resource_uow: ResourceUnitOfWork,
        entry_repo_uow: EntryUowRepositoryUnitOfWork
    ) -> CommandHandler[commands.AddEntry]:
        return AddingEntry(
            resource_uow=resource_uow,
            entry_repo_uow=entry_repo_uow
        )

    @injector.provider
    def add_entries(
        self,
        resource_uow: ResourceUnitOfWork,
        entry_repo_uow: EntryUowRepositoryUnitOfWork
    ) -> CommandHandler[commands.AddEntries]:
        return AddingEntries(
            resource_uow=resource_uow,
            entry_repo_uow=entry_repo_uow
        )

    @injector.provider
    def update_entry(
        self,
        resource_uow: ResourceUnitOfWork,
        entry_repo_uow: EntryUowRepositoryUnitOfWork
    ) -> CommandHandler[commands.UpdateEntry]:
        return UpdatingEntry(
            resource_uow=resource_uow,
            entry_repo_uow=entry_repo_uow
        )

    @injector.provider
    def delete_entry(
        self,
        resource_uow: ResourceUnitOfWork,
        entry_repo_uow: EntryUowRepositoryUnitOfWork
    ) -> CommandHandler[commands.DeleteEntry]:
        return DeletingEntry(
            resource_uow=resource_uow,
            entry_repo_uow=entry_repo_uow
        )
