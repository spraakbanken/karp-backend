import injector  # noqa: I001
import pytest

from karp.foundation.events import EventBus
from karp.lex_infrastructure import GenericLexInfrastructure
from karp.main.modules import CommandsMod, EventBusMod
from karp.search import Search
from karp.search_infrastructure import SearchInfrastructure, GenericSearchInfrastructure
from tests.unit.lex.adapters import InMemoryLexInfrastructure

from . import adapters


@pytest.fixture()
def search_unit_ctx() -> adapters.SearchUnitTestContext:
    container = injector.Injector(
        [
            CommandsMod(),
            EventBusMod(),
            Search(),
            SearchInfrastructure(),
            GenericLexInfrastructure(),
            InMemoryLexInfrastructure(),
            GenericSearchInfrastructure(),
            adapters.InMemorySearchInfrastructure(),
        ],
        auto_bind=False,
    )
    return adapters.SearchUnitTestContext(
        container=container,
        event_bus=container.get(EventBus),  # type: ignore
    )
