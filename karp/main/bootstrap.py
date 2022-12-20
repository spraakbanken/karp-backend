from karp.foundation import messagebus
from karp.lex.application import (
    handlers as lex_handlers,
    repositories as lex_repositories,
)
from karp.lex.domain import commands as lex_commands, events as lex_events
from karp.search.application import handlers as search_handlers
from karp.search.application.unit_of_work import SearchServiceUnitOfWork
from karp.lex.application import repositories


def bootstrap_message_bus(
    *,
    resource_uow: repositories.ResourceUnitOfWork,
    entry_uows: repositories.EntriesUnitOfWork,
    entry_uow_factory,  #: repositories.EntryUowFactory,
    search_service_uow: SearchServiceUnitOfWork,
    entry_repo_repo_uow: lex_repositories.EntryRepositoryRepositoryUnitOfWork,
    raise_on_all_errors: bool = False
) -> messagebus.MessageBus:
    return messagebus.MessageBus(
        command_handlers={
            lex_commands.CreateResource: lex_handlers.CreateResourceHandler(
                resource_uow=resource_uow,
                entry_repo_repo_uow=entry_repo_repo_uow,
            ),
            lex_commands.PublishResource: lex_handlers.PublishResourceHandler(
                resource_uow=resource_uow,
            ),
            lex_commands.UpdateResource: lex_handlers.UpdateResourceHandler(
                resource_uow=resource_uow,
            ),
            # Entry command handlers
            lex_commands.AddEntry: lex_handlers.AddEntryHandler(
                resource_uow=resource_uow,
                entry_uows=entry_uows,
            ),
            lex_commands.DeleteEntry: lex_handlers.DeleteEntryHandler(
                resource_uow=resource_uow,
                entry_uows=entry_uows,
            ),
            lex_commands.UpdateEntry: lex_handlers.UpdateEntryHandler(
                resource_uow=resource_uow,
                entry_uows=entry_uows,
            ),
        },
        event_handlers={
            lex_events.ResourceCreated: [
                search_handlers.CreateIndexHandler(
                    search_service_uow=search_service_uow
                ),
            ],
            lex_events.ResourcePublished: [],
            lex_events.ResourceUpdated: [],
            lex_events.EntryAdded: [],
            lex_events.EntryDeleted: [],
            lex_events.EntryUpdated: [],
        },
        raise_on_all_errors=raise_on_all_errors,
    )
