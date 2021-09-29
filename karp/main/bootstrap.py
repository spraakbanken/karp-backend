from karp.foundation import messagebus
from karp.lex.application import command_handlers as lex_cmd_handlers
from karp.lex.domain import commands as lex_commands, events as lex_events
from karp.services import unit_of_work


def bootstrap_message_bus(
    *,
    resource_uow: unit_of_work.ResourceUnitOfWork,
    entry_uows: unit_of_work.EntriesUnitOfWork,
    entry_uow_factory: unit_of_work.EntryUowFactory,
    raise_on_all_errors: bool = False
) -> messagebus.MessageBus:
    return messagebus.MessageBus(
        command_handlers={
            lex_commands.CreateResource: lex_cmd_handlers.CreateResourceHandler(
                resource_uow=resource_uow,
                entry_uow_factory=entry_uow_factory,
                entry_uows=entry_uows
            ),
            lex_commands.PublishResource: lex_cmd_handlers.PublishResourceHandler(
                resource_uow=resource_uow,
            ),
            lex_commands.UpdateResource: lex_cmd_handlers.UpdateResourceHandler(
                resource_uow=resource_uow,
            ),
            # Entry command handlers
            lex_commands.AddEntry: lex_cmd_handlers.AddEntryHandler(
                resource_uow=resource_uow,
                entry_uows=entry_uows,
            ),
            lex_commands.DeleteEntry: lex_cmd_handlers.DeleteEntryHandler(
                resource_uow=resource_uow,
                entry_uows=entry_uows,
            ),
            lex_commands.UpdateEntry: lex_cmd_handlers.UpdateEntryHandler(
                resource_uow=resource_uow,
                entry_uows=entry_uows,
            )
        },
        event_handlers={
            lex_events.ResourceCreated: [],
            lex_events.ResourcePublished: [],
            lex_events.ResourceUpdated: [],
            lex_events.EntryAdded: [],
            lex_events.EntryDeleted: [],
            lex_events.EntryUpdated: [],
        },
        raise_on_all_errors=raise_on_all_errors)
