from karp.services import unit_of_work
from karp.foundation import messagebus

from karp.lex.application.handlers import (
    CreateResourceHandler,
    PublishResourceHandler,
    UpdateResourceHandler,
    AddEntryHandler,
)
from karp.lex.domain import commands


def bootstrap_message_bus(
    *,
    resource_uow: unit_of_work.ResourceUnitOfWork,
    entry_uows: unit_of_work.EntriesUnitOfWork,
    entry_uow_factory: unit_of_work.EntryUowFactory,
    raise_on_all_errors: bool = False
) -> messagebus.MessageBus:
    return messagebus.MessageBus(
        command_handlers={
            commands.CreateResource: CreateResourceHandler(
                resource_uow=resource_uow,
                entry_uow_factory=entry_uow_factory,
                entry_uows=entry_uows
            ),
            commands.PublishResource: PublishResourceHandler(
                resource_uow=resource_uow,
            ),
            commands.UpdateResource: UpdateResourceHandler(
                resource_uow=resource_uow,
            ),
            # Entry command handlers
            commands.AddEntry: AddEntryHandler(
                resource_uow=resource_uow,
                entry_uows=entry_uows,
            )},
        event_handlers={},
        raise_on_all_errors=raise_on_all_errors)
