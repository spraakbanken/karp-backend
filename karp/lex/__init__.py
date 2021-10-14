import injector

from karp.foundation.commands import CommandHandler
from karp.lex.application import handlers
from karp.lex.application.repositories import (
    EntryUowRepositoryUnitOfWork,
    EntryRepositoryUnitOfWorkFactory,
    ResourceUnitOfWork,
)
from karp.lex.domain.commands import (
    CreateEntryRepository,
    CreateResource,
)


class Lex(injector.Module):
    @injector.provider
    def create_entry_repository(
        self,
        uow: EntryUowRepositoryUnitOfWork,
        uow_factory: EntryRepositoryUnitOfWorkFactory,
    ) -> CommandHandler[CreateEntryRepository]:
        return handlers.CreateEntryRepositoryHandler(uow, uow_factory)

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
