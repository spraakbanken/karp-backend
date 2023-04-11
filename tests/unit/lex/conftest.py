import injector  # noqa: I001
import pytest

from karp.command_bus import CommandBus
from karp.lex import Lex
from karp.main.modules import CommandBusMod, EventBusMod
from . import adapters, factories  # noqa: F401


@pytest.fixture()
def lex_ctx() -> adapters.UnitTestContext:
    container = injector.Injector(
        [
            CommandBusMod(),
            EventBusMod(),
            Lex(),
            adapters.InMemoryLexInfrastructure(),
        ],
        auto_bind=False,
    )
    return adapters.UnitTestContext(
        container=container,
        command_bus=container.get(CommandBus),  # type: ignore [misc]
    )


@pytest.fixture()
def command_bus(unit_test_injector: injector.Injector) -> CommandBus:
    return unit_test_injector.get(CommandBus)  # type: ignore [misc]
