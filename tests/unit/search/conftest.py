import injector  # noqa: I001
import pytest

from tests.unit.lex.adapters import InMemoryLexInfrastructure

from . import adapters


@pytest.fixture()
def search_unit_ctx() -> adapters.SearchUnitTestContext:
    container = injector.Injector(
        [
            InMemoryLexInfrastructure(),
            adapters.InMemorySearchInfrastructure(),
        ]
    )
    return adapters.SearchUnitTestContext(
        container=container,
    )
