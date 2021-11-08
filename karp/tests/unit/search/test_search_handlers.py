from typing import Callable

import pytest

from karp.lex.domain.events import ResourceCreated

from karp.search.application.repositories import SearchServiceUnitOfWork
from karp.tests.unit.lex import factories as lex_factories
from . import adapters


@pytest.fixture(name="resource_created")
def fixture_resource_created() -> ResourceCreated:
    return lex_factories.ResourceCreatedFactory()


@pytest.mark.parametrize('event_factory,predicate', [
    (None, lambda x: x.created),
    (lex_factories.ResourcePublishedFactory, lambda x: x.published),
    (lex_factories.EntryAddedFactory, lambda x: len(x.entries) == 1 ),

])
def test_index_reacts_on_lex_events(
    event_factory,
    predicate: Callable,
    search_unit_ctx: adapters.SearchUnitTestContext,
):
    resource_created = lex_factories.ResourceCreatedFactory()
    search_unit_ctx.event_bus.post(resource_created)
    if event_factory:
        event = event_factory(resource_id=resource_created.resource_id)
        search_unit_ctx.event_bus.post(event)

    search_service_uow = search_unit_ctx.container.get(
        SearchServiceUnitOfWork)
    assert search_service_uow.was_committed

    assert predicate(search_service_uow.repo.indicies[resource_created.resource_id])


def test_transform_to_index_entry():
    pass
