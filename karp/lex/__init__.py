import injector

from karp.foundation.commands import CommandHandler
from karp.lex.application import handlers
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
from karp.lex.application.use_cases import (
    AddingEntry,
    CreatingEntryRepo,
    CreatingResource,
)
from karp.lex.application.queries import (
    GetEntryDiff,
    GetEntryHistory,
    GetHistory,
    GetPublishedResources,
    ResourceDto,
    ReadOnlyResourceRepository,
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
        return handlers.CreateEntryRepositoryHandler(
            entry_repo_uow=uow,
        )

    @injector.provider
    def create_resource(
        self,
        entry_uow_repo_uow: EntryUowRepositoryUnitOfWork,
        resource_uow: ResourceUnitOfWork,
    ) -> CommandHandler[CreateResource]:
        return handlers.CreateResourceHandler(
            entry_uow_repo_uow=entry_uow_repo_uow,
            resource_uow=resource_uow,
        )

    @injector.provider
    def update_resource(
        self,
        resource_uow: ResourceUnitOfWork,
    ) -> CommandHandler[commands.UpdateResource]:
        return handlers.UpdateResourceHandler(resource_uow)

    @injector.provider
    def publish_resource(
        self,
        resource_uow: ResourceUnitOfWork,
    ) -> CommandHandler[commands.PublishResource]:
        return handlers.PublishResourceHandler(resource_uow)

    @injector.provider
    def add_entry(
        self,
        resource_uow: ResourceUnitOfWork,
        entry_uow_repo_uow: EntryUowRepositoryUnitOfWork
    ) -> CommandHandler[commands.AddEntry]:
        return handlers.AddEntryHandler(
            resource_uow=resource_uow,
            entry_uow_repo_uow=entry_uow_repo_uow
        )

    @injector.provider
    def add_entries(
        self,
        resource_uow: ResourceUnitOfWork,
        entry_uow_repo_uow: EntryUowRepositoryUnitOfWork
    ) -> CommandHandler[commands.AddEntries]:
        return handlers.AddEntriesHandler(
            resource_uow=resource_uow,
            entry_uow_repo_uow=entry_uow_repo_uow
        )

    @injector.provider
    def update_entry(
        self,
        resource_uow: ResourceUnitOfWork,
        entry_uow_repo_uow: EntryUowRepositoryUnitOfWork
    ) -> CommandHandler[commands.UpdateEntry]:
        return handlers.UpdateEntryHandler(
            resource_uow=resource_uow,
            entry_uow_repo_uow=entry_uow_repo_uow
        )

    @injector.provider
    def delete_entry(
        self,
        resource_uow: ResourceUnitOfWork,
        entry_uow_repo_uow: EntryUowRepositoryUnitOfWork
    ) -> CommandHandler[commands.DeleteEntry]:
        return handlers.DeleteEntryHandler(
            resource_uow=resource_uow,
            entry_uow_repo_uow=entry_uow_repo_uow
        )
