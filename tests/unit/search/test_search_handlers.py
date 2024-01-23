from typing import Callable  # noqa: I001

import pytest

from karp.lex.domain.events import ResourceCreated

from karp.search.application.repositories import IndexUnitOfWork
from tests.unit.lex import factories as lex_factories
from . import adapters, factories


@pytest.fixture(name="resource_created")
def fixture_resource_created() -> ResourceCreated:
    return lex_factories.ResourceCreatedFactory()  # type: ignore [return-value]


@pytest.mark.parametrize(
    "event_factory,predicate",
    [
        (None, lambda x: x.created),
        (lex_factories.ResourcePublishedFactory, lambda x: x.published),
    ],
)
def test_index_reacts_on_lex_events(  # noqa: ANN201
    event_factory,
    predicate: Callable,
    search_unit_ctx: adapters.SearchUnitTestContext,
):
    resource_created = lex_factories.ResourceCreatedFactory()
    search_unit_ctx.event_bus.post(resource_created)  # type: ignore [arg-type]
    if event_factory:
        event = event_factory(resourceId=resource_created.resource_id)
        search_unit_ctx.event_bus.post(event)

    index_uow = search_unit_ctx.container.get(IndexUnitOfWork)  # type: ignore [misc]
    assert index_uow.was_committed  # type: ignore [attr-defined]

    assert predicate(index_uow.repo.indicies[resource_created.resource_id])  # type: ignore [attr-defined]
