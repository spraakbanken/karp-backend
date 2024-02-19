import injector  # noqa: I001
import pytest

from karp.main.modules import CommandsMod, GenericLexInfrastructure
from tests.unit.lex.adapters import InMemoryLexInfrastructure

from . import adapters


@pytest.fixture()
def search_unit_ctx() -> adapters.SearchUnitTestContext:
    container = injector.Injector(
        [
            CommandsMod(),
            GenericLexInfrastructure(),
            InMemoryLexInfrastructure(),
            adapters.InMemorySearchInfrastructure(),
        ],
        auto_bind=False,
    )
    return adapters.SearchUnitTestContext(
        container=container,
    )
