from injector import Injector
import pytest

from . import adapters


@pytest.fixture()
def search_unit_ctx() -> adapters.SearchUnitTestContext:
    injector = Injector(
        [
            adapters.InMemorySearchInfrastructure(),
        ]
    )
    return adapters.SearchUnitTestContext(
        injector=injector,
    )
