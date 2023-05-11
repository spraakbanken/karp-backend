import injector  # noqa: I001

from karp.command_bus import CommandBus, CommandHandler
from karp.lex.application.repositories import (
    EntryUowRepositoryUnitOfWork,
    EntryRepositoryUnitOfWorkFactory,
    InjectorEntryUnitOfWorkRepoFactory,
    ResourceUnitOfWork,
)
from karp.lex_core.commands import (
    AddEntries,
    AddEntriesInChunks,
    AddEntry,
    CreateEntryRepository,
    CreateResource,
    ImportEntries,
    ImportEntriesInChunks,
    SetEntryRepoId,
    EntryCommand,
    ExecuteBatchOfEntryCommands,
)
from karp.lex_core import commands
from karp.lex.domain.value_objects import EntrySchema
from karp.lex.application.use_cases import (
    AddingEntries,
    AddingEntry,
    CreatingEntryRepo,
    CreatingResource,
    DeletingEntry,
    DeletingResource,
    ImportingEntries,
    PublishingResource,
    SettingEntryRepoId,
    UpdatingEntry,
    UpdatingResource,
    ExecutingBatchOfEntryCommands,
)
from karp.lex.application.queries import (
    EntryDto,
    EntryViews,
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
    ReadOnlyEntryRepoRepository,
    ListEntryRepos,
)


__all__ = [
    # modules
    "commands",
    # commands
    "AddEntries",
    "AddEntriesInChunks",
    "AddEntry",
    "ImportEntries",
    "ImportEntriesInChunks",
    "CreateEntryRepository",
    "EntryCommand",
    "ExecuteBatchOfEntryCommands",
    # use cases
    "CreatingEntryRepo",
    "CreatingResource",
    "ImportingEntries",
    # dtos
    "EntryDto",
    "GetHistoryDto",
    "ResourceDto",
    "HistoryDto",
    # queries
    "GetResources",
    # repositories
    "ResourceUnitOfWork",
    # value objects
    "EntrySchema",
]


class Lex(injector.Module):  # noqa: D101
    @injector.provider
    def entry_uow_factory(  # noqa: D102
        self, container: injector.Injector
    ) -> EntryRepositoryUnitOfWorkFactory:
        return InjectorEntryUnitOfWorkRepoFactory(container)

    @injector.provider
    def create_entry_repository(  # noqa: D102
        self,
        uow: EntryUowRepositoryUnitOfWork,
    ) -> CommandHandler[CreateEntryRepository]:
        return CreatingEntryRepo(
            entry_repo_uow=uow,
        )

    @injector.provider
    def create_resource(  # noqa: D102
        self,
        entry_repo_uow: EntryUowRepositoryUnitOfWork,
        resource_uow: ResourceUnitOfWork,
    ) -> CommandHandler[CreateResource]:
        return CreatingResource(
            entry_repo_uow=entry_repo_uow,
            resource_uow=resource_uow,
        )

    @injector.provider
    def deleting_resource(  # noqa: D102
        self,
        resource_uow: ResourceUnitOfWork,
        entry_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> CommandHandler[commands.DeleteResource]:
        return DeletingResource(resource_uow, entry_repo_uow)

    @injector.provider
    def setting_entry_repo_id(  # noqa: D102
        self,
        entry_repo_uow: EntryUowRepositoryUnitOfWork,
        resource_uow: ResourceUnitOfWork,
    ) -> CommandHandler[SetEntryRepoId]:
        return SettingEntryRepoId(
            entry_repo_uow=entry_repo_uow,
            resource_uow=resource_uow,
        )

    @injector.provider
    def update_resource(  # noqa: D102
        self,
        resource_uow: ResourceUnitOfWork,
    ) -> CommandHandler[commands.UpdateResource]:
        return UpdatingResource(resource_uow)

    @injector.provider
    def publish_resource(  # noqa: D102
        self,
        resource_uow: ResourceUnitOfWork,
    ) -> CommandHandler[commands.PublishResource]:
        return PublishingResource(resource_uow)

    @injector.provider
    def add_entry(  # noqa: D102
        self,
        resource_uow: ResourceUnitOfWork,
        entry_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> CommandHandler[commands.AddEntry]:
        return AddingEntry(
            resource_uow=resource_uow,
            entry_repo_uow=entry_repo_uow,
        )

    @injector.provider
    def add_entries(  # noqa: D102
        self,
        resource_uow: ResourceUnitOfWork,
        entry_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> CommandHandler[commands.AddEntries]:
        return AddingEntries(resource_uow=resource_uow, entry_repo_uow=entry_repo_uow)

    @injector.provider
    def adding_entries_in_chunks(  # noqa: D102
        self,
        resource_uow: ResourceUnitOfWork,
        entry_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> CommandHandler[AddEntriesInChunks]:
        return AddingEntries(resource_uow=resource_uow, entry_repo_uow=entry_repo_uow)  # type: ignore[return-value]

    @injector.provider
    def import_entries(  # noqa: D102
        self,
        resource_uow: ResourceUnitOfWork,
        entry_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> CommandHandler[commands.ImportEntries]:
        return ImportingEntries(
            resource_uow=resource_uow, entry_repo_uow=entry_repo_uow
        )

    @injector.provider
    def importing_entries_in_chunks(  # noqa: D102
        self,
        resource_uow: ResourceUnitOfWork,
        entry_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> CommandHandler[ImportEntriesInChunks]:
        return ImportingEntries(  # type: ignore[return-value]
            resource_uow=resource_uow, entry_repo_uow=entry_repo_uow
        )

    @injector.provider
    def update_entry(  # noqa: D102
        self,
        resource_uow: ResourceUnitOfWork,
        entry_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> CommandHandler[commands.UpdateEntry]:
        return UpdatingEntry(
            resource_uow=resource_uow,
            entry_repo_uow=entry_repo_uow,
        )

    @injector.provider
    def delete_entry(  # noqa: D102
        self,
        resource_uow: ResourceUnitOfWork,
        entry_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> CommandHandler[commands.DeleteEntry]:
        return DeletingEntry(resource_uow=resource_uow, entry_repo_uow=entry_repo_uow)

    @injector.provider
    def batch_of_entry_commands(
        self,
        command_bus: CommandBus,
    ) -> CommandHandler[commands.ExecuteBatchOfEntryCommands]:
        return ExecutingBatchOfEntryCommands(command_bus=command_bus)
