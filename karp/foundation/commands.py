import abc
from typing import Generic, TypeVar

import injector


CommandType = TypeVar('CommandType')


class CommandHandler(Generic[CommandType]):
    def __call__(self, command: CommandType) -> None:
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
        cmd_cls = type(command)
        cmd_handler = self._injector.get(
            CommandHandler[cmd_cls])  # type: ignore
        cmd_handler(command)
