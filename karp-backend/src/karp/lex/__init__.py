import injector  # noqa: I001

from karp.command_bus import CommandHandler
from karp.lex.application.repositories import (
    EntryUowRepositoryUnitOfWork,
    ResourceUnitOfWork,
)
from karp.lex_core.commands import (
    CreateEntryRepository,
    CreateResource,
    SetEntryRepoId,
)
from karp.lex_core import commands
from karp.lex.domain.value_objects import EntrySchema
from karp.lex.application.use_cases import (
    CreatingEntryRepo,
    CreatingResource,
    DeletingResource,
    PublishingResource,
    SettingEntryRepoId,
    UpdatingResource,
)
from karp.lex.application.queries import (
    EntryDto,
    GetHistoryDto,
    HistoryDto,
    EntryRepoDto,
)


__all__ = [
    # modules
    "commands",
    # commands
    "CreateEntryRepository",
    # use cases
    "CreatingEntryRepo",
    "CreatingResource",
    # dtos
    "EntryDto",
    "GetHistoryDto",
    "HistoryDto",
    # repositories
    "ResourceUnitOfWork",
    # value objects
    "EntrySchema",
]


class Lex(injector.Module):  # noqa: D101
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
