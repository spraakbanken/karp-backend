import abc
import logging
from typing import Dict, List, Type, Union, TypeVar, Generic, Iterable

from .commands import Command
from .events import Event


logger = logging.getLogger(__name__)

T = TypeVar("T")


class Handler(Generic[T]):
    @abc.abstractmethod
    def execute(self, t: T) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def collect_new_events(self) -> Iterable[Event]:
        raise NotImplementedError


CommandType = TypeVar("CommandType", bound=Command)
EventType = TypeVar("EventType", bound=Event)


class CommandHandler(Generic[CommandType], Handler[CommandType]):
    pass


Message = Union[Command, Event]


class MessageBus:
    def __init__(
        self,
        command_handlers: Dict[Type[Command], CommandHandler[Command]],
        event_handlers: Dict[Type[Event], List[Handler[Event]]],
        raise_on_all_errors: bool = False,
    ) -> None:
        self._command_handlers = command_handlers
        self._event_handlers = event_handlers
        self.raise_on_all_errors = raise_on_all_errors
        self.queue: List[Message] = []

    def handle(self, msg: Message):
        self.queue = [msg]
        while self.queue:
            msg = self.queue.pop(0)
            if isinstance(msg, Event):
                self._handle_event(msg)
            elif isinstance(msg, Command):
                self._handle_command(msg)
            else:
                raise Exception(f"{msg} was not an Event or Command")

    def _handle_event(self, event: Event):
        for evt_handler in self._event_handlers[type(event)]:
            logger.debug("handling event %s with handler %s", event, evt_handler)
            try:
                evt_handler.execute(event)
            except Exception:
                logger.exception("Exception handling event %s", event)
                if self.raise_on_all_errors:
                    raise
            else:
                self.queue.extend(evt_handler.collect_new_events())

    def _handle_command(self, command: Command):
        logger.debug("handling command %s", command)
        cmd_handler = self._command_handlers[type(command)]
        try:
            cmd_handler.execute(command)
        except Exception:
            logger.exception("Exception handling command %s", command)
            raise
        self.queue.extend(cmd_handler.collect_new_events())
