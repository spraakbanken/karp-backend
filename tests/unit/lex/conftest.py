import injector  # noqa: I001
import pytest

from . import adapters


@pytest.fixture()
def lex_ctx() -> adapters.UnitTestContext:
    container = injector.Injector(
        [
            adapters.InMemoryLexInfrastructure(),
        ]
    )
    return adapters.UnitTestContext(
        container=container,
    )
