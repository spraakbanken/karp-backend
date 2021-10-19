import injector
import pytest

from karp.foundation.commands import CommandBus
from karp.foundation.events import EventBus
from karp.main.modules import CommandBusMod, EventBusMod
from karp.search import Search

from . import adapters


@pytest.fixture()
def search_unit_ctx() -> adapters.SearchUnitTestContext:
    container = injector.Injector([
        CommandBusMod(),
        EventBusMod(),
        Search(),
        adapters.FakeSearchInfrastructure(),
    ], auto_bind=False)
    return adapters.SearchUnitTestContext(
        container=container,
        command_bus=container.get(CommandBus),
        event_bus=container.get(EventBus)
    )
