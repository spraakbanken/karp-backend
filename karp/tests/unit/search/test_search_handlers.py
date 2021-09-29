import pytest

from karp.lex.domain.events import ResourceCreated


from karp.tests.unit import factories
from karp.tests.unit.adapters import bootstrap_test_app, FakeSearchServiceUnitOfWork


@pytest.fixture(name="resource_created")
def fixture_resource_created() -> ResourceCreated:
    return factories.ResourceCreatedFactory()


class TestSearchServiceReactsOnLexEvents:
    def test_ResourceCreated(
        self,
        resource_created: ResourceCreated,
        search_service_uow: FakeSearchServiceUnitOfWork
    ):
        bus = bootstrap_test_app(search_service_uow=search_service_uow)

        bus.handle(resource_created)

        assert search_service_uow.repo.indicies[resource_created.resource_id].created


def test_transform_to_index_entry():
    pass
