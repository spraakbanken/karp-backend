import abc
import logging
from typing import Any, Generic, TypeVar

import injector


CommandType = TypeVar('CommandType')


logger = logging.getLogger(__name__)


class CommandHandler(Generic[CommandType]):
    def execute(self, command: CommandType) -> Any:
        raise NotImplementedError()


class Command:
    pass


class CommandBus(abc.ABC):
    @abc.abstractmethod
    def dispatch(self, command: Command) -> None:
        raise NotImplementedError


class InjectorCommandBus(CommandBus):
    def __init__(self, injector: injector.Injector) -> None:
        self._injector = injector

    def dispatch(self, command: Command) -> None:
        logger.info('Handling command: %s', command)
        cmd_cls = type(command)
        cmd_handler = self._injector.get(
            CommandHandler[cmd_cls])  # type: ignore

        logger.info('Handling command %s with handler %s',
                    command, cmd_handler)
        cmd_handler.execute(command)
