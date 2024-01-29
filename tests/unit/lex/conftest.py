import injector  # noqa: I001
import pytest

from karp.main.modules import CommandsMod, EventBusMod
from . import adapters


@pytest.fixture()
def lex_ctx() -> adapters.UnitTestContext:
    container = injector.Injector(
        [
            CommandsMod(),
            EventBusMod(),
            adapters.InMemoryLexInfrastructure(),
        ],
        auto_bind=False,
    )
    return adapters.UnitTestContext(
        container=container,
    )
