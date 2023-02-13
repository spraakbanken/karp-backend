import injector

from karp.command_bus import CommandHandler
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
    DeleteEntryRepository,
    ImportEntries,
    ImportEntriesInChunks,
    SetEntryRepoId,
)
from karp.lex_core import commands
from karp.lex.domain.value_objects import EntrySchema  # noqa: F401
from karp.lex.application.use_cases import (
    AddingEntries,
    AddingEntry,
    CreatingEntryRepo,
    CreatingResource,
    DeletingEntry,
    DeletingEntryRepository,
    DeletingResource,
    ImportingEntries,
    PublishingResource,
    SettingEntryRepoId,
    UpdatingEntry,
    UpdatingResource,
)
from karp.lex.application.queries import (
    EntryDto,  # noqa: F401
    EntryViews,  # noqa: F401
    GetEntryDiff,  # noqa: F401
    GetEntryHistory,  # noqa: F401
    GetHistory,  # noqa: F401
    GetHistoryDto,  # noqa: F401
    GetPublishedResources,  # noqa: F401
    GetResources,
    HistoryDto,  # noqa: F401
    ResourceDto,
    ReadOnlyResourceRepository,  # noqa: F401
    EntryRepoDto,  # noqa: F401
    ReadOnlyEntryRepoRepository,  # noqa: F401
    ListEntryRepos,  # noqa: F401
)


__all__ = [
    # modules
    "commands",
    # commands
    "commands",
    "AddEntries",
    "AddEntriesInChunks",
    "AddEntry",
    "ImportEntries",
    "ImportEntriesInChunks",
    "CreateEntryRepository",
    # use cases
    "CreatingEntryRepo",
    "CreatingResource",
    "ImportingEntries",
    # dtos
    "ResourceDto",
    # queries
    "GetResources",
]


class Lex(injector.Module):
    @injector.provider
    def entry_uow_factory(
        self, container: injector.Injector
    ) -> EntryRepositoryUnitOfWorkFactory:
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
    def deleting_entry_repository(
        self,
        uow: EntryUowRepositoryUnitOfWork,
    ) -> CommandHandler[DeleteEntryRepository]:
        return DeletingEntryRepository(
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
    def deleting_resource(
        self,
        resource_uow: ResourceUnitOfWork,
    ) -> CommandHandler[commands.DeleteResource]:
        return DeletingResource(resource_uow)

    @injector.provider
    def setting_entry_repo_id(
        self,
        entry_repo_uow: EntryUowRepositoryUnitOfWork,
        resource_uow: ResourceUnitOfWork,
    ) -> CommandHandler[SetEntryRepoId]:
        return SettingEntryRepoId(
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
        entry_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> CommandHandler[commands.AddEntry]:
        return AddingEntry(resource_uow=resource_uow, entry_repo_uow=entry_repo_uow)

    @injector.provider
    def add_entries(
        self,
        resource_uow: ResourceUnitOfWork,
        entry_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> CommandHandler[commands.AddEntries]:
        return AddingEntries(resource_uow=resource_uow, entry_repo_uow=entry_repo_uow)

    @injector.provider
    def adding_entries_in_chunks(
        self,
        resource_uow: ResourceUnitOfWork,
        entry_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> CommandHandler[AddEntriesInChunks]:
        return AddingEntries(resource_uow=resource_uow, entry_repo_uow=entry_repo_uow)

    @injector.provider
    def import_entries(
        self,
        resource_uow: ResourceUnitOfWork,
        entry_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> CommandHandler[commands.ImportEntries]:
        return ImportingEntries(
            resource_uow=resource_uow, entry_repo_uow=entry_repo_uow
        )

    @injector.provider
    def importing_entries_in_chunks(
        self,
        resource_uow: ResourceUnitOfWork,
        entry_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> CommandHandler[ImportEntriesInChunks]:
        return ImportingEntries(
            resource_uow=resource_uow, entry_repo_uow=entry_repo_uow
        )

    @injector.provider
    def update_entry(
        self,
        resource_uow: ResourceUnitOfWork,
        entry_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> CommandHandler[commands.UpdateEntry]:
        return UpdatingEntry(resource_uow=resource_uow, entry_repo_uow=entry_repo_uow)

    @injector.provider
    def delete_entry(
        self,
        resource_uow: ResourceUnitOfWork,
        entry_repo_uow: EntryUowRepositoryUnitOfWork,
    ) -> CommandHandler[commands.DeleteEntry]:
        return DeletingEntry(resource_uow=resource_uow, entry_repo_uow=entry_repo_uow)
