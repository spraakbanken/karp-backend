import pytest
from injector import Injector

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
