import injector

from karp.foundation.commands import CommandHandler
from karp.lex.application import handlers
from karp.lex.application.repositories import (
    EntryUowRepositoryUnitOfWork,
    EntryRepositoryUnitOfWorkFactory,
)
from karp.lex.domain.commands import (
    CreateEntryRepository,
)


class Lex(injector.Module):
    @injector.provider
    def create_entry_repository(
        self,
        uow: EntryUowRepositoryUnitOfWork,
        uow_factory: EntryRepositoryUnitOfWorkFactory,
    ) -> CommandHandler[CreateEntryRepository]:
        return handlers.CreateEntryRepositoryHandler(uow, uow_factory)
