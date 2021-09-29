import abc
import logging
import typing
from typing import Dict, List, Type, Union

from .commands import Command
from .events import Event

T = typing.TypeVar("T")


class Handler(typing.Generic[T]):
    @abc.abstractmethod
    def execute(self, t: T) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def collect_new_events(self) -> typing.Iterable[Event]:
        raise NotImplementedError


CommandType = typing.TypeVar('CommandType', bound=Command)
EventType = typing.TypeVar('EventType', bound=Event)


class CommandHandler(typing.Generic[CommandType], Handler[CommandType]):
    pass


class MessageBus:
    def __init__(
        self,
        command_handlers: Dict[Type[Command], CommandHandler[Command]],
        event_handlers: Dict[Type[Event], List[Handler[Event]]],
        logger: logging.Logger = None,
        raise_on_all_errors: bool = False,
    ) -> None:
        self._command_handlers = command_handlers
        self._event_handlers = event_handlers
        self._logger = logger or logging.getLogger(__name__)
        self.raise_on_all_errors = raise_on_all_errors
        self.queue: List[Union[Command, Event]] = []

    def handle(self, msg: typing.Union[Command, Event]):
        self.queue = [msg]
        if isinstance(msg, Event):
            self._handle_event(msg)
        elif isinstance(msg, Command):
            self._handle_command(msg)
        else:
            raise Exception(f"{msg} was not an Event or Command")

    def _handle_event(self, event: Event):
        for handler in self._event_handlers[type(event)]:
            try:
                self._logger.debug(
                    "handling event %s with handler %s", event, handler)
                handler.execute(event)
                self.queue.extend(handler.collect_new_events())
            except Exception:
                self._logger.exception("Exception handling event %s", event)
                if self.raise_on_all_errors:
                    raise
                continue

    def _handle_command(self, command: Command):
        self._logger.debug("handling command %s", command)
        try:
            handler = self._command_handlers[type(command)]
            handler.execute(command)
            self.queue.extend(handler.collect_new_events())
        except Exception:
            self._logger.exception("Exception handling command %s", command)
            raise
