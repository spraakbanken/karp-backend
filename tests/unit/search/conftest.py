import injector  # noqa: I001
import pytest

from karp.lex_infrastructure import GenericLexInfrastructure
from karp.main.modules import CommandsMod
from karp.search_infrastructure import SearchInfrastructure, GenericSearchInfrastructure
from tests.unit.lex.adapters import InMemoryLexInfrastructure

from . import adapters


@pytest.fixture()
def search_unit_ctx() -> adapters.SearchUnitTestContext:
    container = injector.Injector(
        [
            CommandsMod(),
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
    )
