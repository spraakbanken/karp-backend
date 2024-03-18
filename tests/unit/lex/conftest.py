from injector import Injector  # noqa: I001
import pytest

from . import adapters


@pytest.fixture()
def lex_ctx() -> adapters.UnitTestContext:
    injector = Injector(
        [
            adapters.InMemoryLexInfrastructure(),
        ]
    )
    return adapters.UnitTestContext(
        injector=injector,
    )
