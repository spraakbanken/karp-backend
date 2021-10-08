import injector

from karp.foundation.commands import CommandHandler
from karp.lex.application import handlers
from karp.lex.application.unit_of_work import (
    EntryRepositoryRepositoryUnitOfWork,
)
from karp.lex.domain.commands import (
    CreateEntryRepository,
)


class Lex(injector.Module):
    @injector.provider
    def create_entry_repository(
        self,
        uow: EntryRepositoryRepositoryUnitOfWork,
    ) -> CommandHandler[CreateEntryRepository]:
        return handlers.CreateEntryRepositoryHandler(uow)
