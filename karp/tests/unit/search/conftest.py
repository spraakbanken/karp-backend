import injector
import pytest

from karp.foundation.commands import CommandBus
from karp.foundation.events import EventBus
from karp.lex import Lex
from karp.lex_infrastructure import GenericLexInfrastructure
from karp.main.modules import CommandBusMod, EventBusMod
from karp.search import Search
from karp.search_infrastructure import SearchInfrastructure, GenericSearchInfrastructure
from karp.tests.unit.lex.adapters import InMemoryLexInfrastructure

from . import adapters


@pytest.fixture()
def search_unit_ctx() -> adapters.SearchUnitTestContext:
    container = injector.Injector(
        [
            CommandBusMod(),
            EventBusMod(),
            Search(),
            SearchInfrastructure(),
            Lex(),
            GenericLexInfrastructure(),
            InMemoryLexInfrastructure(),
            GenericSearchInfrastructure(),
            adapters.InMemorySearchInfrastructure(),
        ],
        auto_bind=False,
    )
    return adapters.SearchUnitTestContext(
        container=container,
        command_bus=container.get(CommandBus),  # type: ignore
        event_bus=container.get(EventBus),  # type: ignore
    )
