import pytest

from karp.lex.domain.events import ResourceCreated

from karp.search.application.repositories import SearchServiceUnitOfWork
from karp.tests.unit.lex import factories as lex_factories
from . import adapters


@pytest.fixture(name="resource_created")
def fixture_resource_created() -> ResourceCreated:
    return lex_factories.ResourceCreatedFactory()


class TestSearchServiceReactsOnLexEvents:
    def test_ResourceCreated(
        self,
        resource_created: ResourceCreated,
        search_unit_ctx: adapters.SearchUnitTestContext,
    ):
        search_unit_ctx.event_bus.post(resource_created)

        search_service_uow = search_unit_ctx.container.get(
            SearchServiceUnitOfWork)
        assert search_service_uow.repo.indicies[resource_created.resource_id].created


def test_transform_to_index_entry():
    pass
