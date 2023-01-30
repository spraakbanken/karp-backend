import abc
import logging
from typing import Any, Generic, TypeVar

import injector


CommandType = TypeVar("CommandType")


logger = logging.getLogger(__name__)


class CommandHandler(Generic[CommandType]):
    def execute(self, command: CommandType) -> Any:
        raise NotImplementedError()


class Command:
    pass


class CommandBus(abc.ABC):
    @abc.abstractmethod
    def dispatch(self, command: Command) -> Any:
        raise NotImplementedError


class InjectorCommandBus(CommandBus):
    def __init__(self, container: injector.Injector) -> None:
        self._container = container

    def dispatch(self, command: Command) -> Any:
        logger.info("Handling command: %s", command)
        cmd_cls = type(command)
        cmd_handler = self._container.get(CommandHandler[cmd_cls])  # type: ignore

        logger.info("Handling command %s with handler %s", command, cmd_handler)
        return cmd_handler.execute(command)
