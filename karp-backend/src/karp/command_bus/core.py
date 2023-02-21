import abc  # noqa: D100, I001
import logging
from typing import Any, Generic, TypeVar

import injector


CommandType = TypeVar("CommandType")


logger = logging.getLogger(__name__)


class CommandHandler(Generic[CommandType]):  # noqa: D101
    def execute(self, command: CommandType) -> Any:  # noqa: D102, ANN401
        raise NotImplementedError()


class CommandBus(abc.ABC):  # noqa: D101
    @abc.abstractmethod
    def dispatch(self, command: Any) -> Any:  # noqa: D102, ANN401
        raise NotImplementedError


class InjectorCommandBus(CommandBus):  # noqa: D101
    def __init__(self, container: injector.Injector) -> None:  # noqa: D107
        self._container = container

    def dispatch(self, command: Any) -> Any:  # noqa: D102, ANN401
        logger.info("Handling command: %s", command)
        cmd_cls = type(command)
        cmd_handler = self._container.get(CommandHandler[cmd_cls])  # type: ignore

        logger.info("Handling command %s with handler %s", command, cmd_handler)
        return cmd_handler.execute(command)
