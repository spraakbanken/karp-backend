import injector  # noqa: I001

from karp.command_bus import CommandHandler
from karp.lex.application.repositories import (
    EntryUowRepositoryUnitOfWork,
    ResourceUnitOfWork,
)
from karp.lex_core.commands import (
    CreateEntryRepository,
)
from karp.lex_core import commands
from karp.lex.domain.value_objects import EntrySchema
from karp.lex.application.use_cases import (
    CreatingEntryRepo,
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
    # dtos
    "EntryDto",
    "GetHistoryDto",
    "HistoryDto",
    # repositories
    "ResourceUnitOfWork",
    "EntryUowRepositoryUnitOfWork",
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
