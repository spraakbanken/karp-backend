import logging
from typing import List, Union

from karp.domain import commands, events

from karp.services import entry_handlers, resource_handlers

from . import context, unit_of_work


Message = Union[commands.Command, events.Event]


logger = logging.getLogger("karp")


class MessageBus:
    def __init__(
        self,
        resource_uow: unit_of_work.ResourceUnitOfWork
    ):
        self.ctx = context.Context(
            resource_uow=resource_uow
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


EVENT_HANDLERS = {
    events.ResourceCreated: [],
    events.ResourceUpdated: [],
}

COMMAND_HANDLERS = {
    commands.CreateResource: resource_handlers.create_resource,
    commands.UpdateResource: resource_handlers.update_resource,
    commands.AddEntry: entry_handlers.add_entry,
    commands.UpdateEntry: entry_handlers.update_entry,
}
