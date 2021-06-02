import logging
from typing import Callable, Dict, List, Type, Union

from karp.domain import commands, events, auth_service as authenticator

from karp.services import entry_handlers, resource_handlers, index_handlers

from . import context, unit_of_work


Message = Union[commands.Command, events.Event]


logger = logging.getLogger("karp")


class MessageBus:
    def __init__(
        self,
        resource_uow: unit_of_work.ResourceUnitOfWork,
        entry_uows: unit_of_work.EntriesUnitOfWork,
        auth_service: authenticator.AuthService,
        index_uow: unit_of_work.IndexUnitOfWork,
    ):
        self.ctx = context.Context(
            resource_uow=resource_uow,
            entry_uows=entry_uows,
            auth_service=auth_service,
            index_uow=index_uow,
        )
        self.queue = []

    def handle(self, message: Message):
        self.queue = [message]
        while self.queue:
            message = self.queue.pop(0)
            if isinstance(message, events.Event):
                self.handle_event(message)
            elif isinstance(message, commands.Command):
                self.handle_command(message)
            else:
                raise Exception(f"{message} was not an Event or Command")

    def handle_event(self, event: events.Event):
        for handler in EVENT_HANDLERS[type(event)]:
            try:
                logger.debug("handling event %s with handler %s", event, handler)
                handler(event, ctx=self.ctx)
                self.queue.extend(self.ctx.collect_new_events())
            except Exception:
                logger.exception("Exception handling event %s", event)
                continue

    def handle_command(self, command: commands.Command):
        logger.debug("handling command %s", command)
        try:
            handler = COMMAND_HANDLERS[type(command)]
            handler(command, ctx=self.ctx)
            self.queue.extend(self.ctx.collect_new_events())
        except Exception:
            logger.exception("Exception handling command %s", command)
            raise


EVENT_HANDLERS: Dict[Type[events.Event], List[Callable]] = {
    events.ResourceCreated: [index_handlers.create_index],
    events.ResourcePublished: [index_handlers.publish_index],
    events.ResourceUpdated: [],
    events.EntryAdded: [index_handlers.add_entry],
    events.EntryDiscarded: [index_handlers.delete_entry],
    events.EntryUpdated: [index_handlers.update_entry],
}

COMMAND_HANDLERS: Dict[Type[commands.Command], Callable] = {
    commands.CreateResource: resource_handlers.create_resource,
    commands.PublishResource: resource_handlers.publish_resource,
    commands.UpdateResource: resource_handlers.update_resource,
    commands.AddEntry: entry_handlers.add_entry,
    commands.DeleteEntry: entry_handlers.delete_entry,
    commands.UpdateEntry: entry_handlers.update_entry,
}
