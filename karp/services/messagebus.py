import logging
from typing import List, Union

from karp.domain import commands, events

from karp.services import handlers

from karp.infrastructure import unit_of_work


Message = Union[commands.Command, events.Event]


logger = logging.getLogger("karp")


def handle(message: Message, uow: unit_of_work.UnitOfWork):
    queue = [message]
    while queue:
        message = queue.pop(0)
        if isinstance(message, events.Event):
            handle_event(message, queue, uow)
        elif isinstance(message, commands.Command):
            handle_command(message, queue, uow)
        else:
            raise Exception(f"{message} was not an Event or Command")


def handle_event(
    event: events.Event,
    queue: List[Message],
    uow: unit_of_work.UnitOfWork,
):
    for handler in EVENT_HANDLERS[type(event)]:
        try:
            logger.debug("handling event %s with handler %s", event, handler)
            handler(event, uow=uow)
            queue.extend(uow.collect_new_events())
        except Exception:
            logger.exception("Exception handling event %s", event)
            continue


def handle_command(
    command: commands.Command,
    queue: List[Message],
    uow: unit_of_work.UnitOfWork,
):
    logger.debug("handling command %s", command)
    try:
        handler = COMMAND_HANDLERS[type(command)]
        handler(command, uow=uow)
        queue.extend(uow.collect_new_events())
    except Exception:
        logger.exception("Exception handling command %s", command)
        raise


EVENT_HANDLERS = {
    events.ResourceCreated: [],
}

COMMAND_HANDLERS = {
    commands.CreateResource: handlers.create_resource,
    commands.UpdateResource: handlers.update_resource,
}
