from typing import Callable

import pytest

from karp.lex.domain.events import ResourceCreated

from karp.search.application.repositories import IndexUnitOfWork
from karp.tests.unit.lex import factories as lex_factories
from . import adapters, factories


@pytest.fixture(name="resource_created")
def fixture_resource_created() -> ResourceCreated:
    return lex_factories.ResourceCreatedFactory()


@pytest.mark.parametrize('event_factory,predicate', [
    (None, lambda x: x.created),
    (lex_factories.ResourcePublishedFactory, lambda x: x.published),

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

    index_uow = search_unit_ctx.container.get(
        IndexUnitOfWork)
    assert index_uow.was_committed

    assert predicate(
        index_uow.repo.indicies[resource_created.resource_id])


def test_index_reacts_on_entry_added_event(
    search_unit_ctx: adapters.SearchUnitTestContext,
):
    create_entry_repo = lex_factories.CreateEntryRepositoryFactory()
    search_unit_ctx.command_bus.dispatch(create_entry_repo)
    create_resource = lex_factories.CreateResourceFactory(
        entry_repo_id=create_entry_repo.entity_id)
    search_unit_ctx.command_bus.dispatch(create_resource)
    create_entry = lex_factories.AddEntryFactory(
        resource_id=create_resource.resource_id,
        entry={'baseform': 'bra'},
    )
    search_unit_ctx.command_bus.dispatch(create_entry)
    # if event_factory:
    #     event = event_factory(resource_id=create_resource.resource_id)
    #     search_unit_ctx.event_bus.post(event)

    index_uow = search_unit_ctx.container.get(
        IndexUnitOfWork)
    assert index_uow.was_committed

    assert index_uow.repo.indicies[create_resource.resource_id].created
    assert len(
        index_uow.repo.indicies[create_resource.resource_id].entries) == 1
    assert 'bra' in index_uow.repo.indicies[
        create_resource.resource_id
    ].entries


def test_index_reacts_on_entry_updated_event(
    search_unit_ctx: adapters.SearchUnitTestContext,
):
    create_entry_repo = lex_factories.CreateEntryRepositoryFactory()
    search_unit_ctx.command_bus.dispatch(create_entry_repo)
    create_resource = lex_factories.CreateResourceFactory(
        entry_repo_id=create_entry_repo.entity_id)
    search_unit_ctx.command_bus.dispatch(create_resource)
    create_entry = lex_factories.AddEntryFactory(
        resource_id=create_resource.resource_id,
        entry={'baseform': 'bra'},
    )
    search_unit_ctx.command_bus.dispatch(create_entry)

    update_entry = lex_factories.UpdateEntryFactory(
        resource_id=create_resource.resource_id,
        entry_id='bra',
        entry={'baseform': 'bra', 'wordclass': 'adjektiv'},
        version=1,
    )
    search_unit_ctx.command_bus.dispatch(update_entry)

    index_uow = search_unit_ctx.container.get(
        IndexUnitOfWork)
    assert index_uow.was_committed

    assert index_uow.repo.indicies[create_resource.resource_id].created
    assert len(
        index_uow.repo.indicies[create_resource.resource_id].entries) == 1
    entry = index_uow.repo.indicies[
        create_resource.resource_id
    ].entries['bra']
    assert entry.entry['wordclass'] == 'adjektiv'


def test_index_reacts_on_entry_deleted_event(
    search_unit_ctx: adapters.SearchUnitTestContext,
):
    create_entry_repo = lex_factories.CreateEntryRepositoryFactory()
    search_unit_ctx.command_bus.dispatch(create_entry_repo)
    create_resource = lex_factories.CreateResourceFactory(
        entry_repo_id=create_entry_repo.entity_id)
    search_unit_ctx.command_bus.dispatch(create_resource)
    create_entry = lex_factories.AddEntryFactory(
        resource_id=create_resource.resource_id,
        entry={'baseform': 'bra'},
    )
    search_unit_ctx.command_bus.dispatch(create_entry)

    delete_entry = lex_factories.DeleteEntryFactory(
        resource_id=create_resource.resource_id,
        entry_id='bra',
        version=1,
    )
    search_unit_ctx.command_bus.dispatch(delete_entry)

    index_uow = search_unit_ctx.container.get(
        IndexUnitOfWork)
    assert index_uow.was_committed

    assert index_uow.repo.indicies[create_resource.resource_id].created
    assert len(
        index_uow.repo.indicies[create_resource.resource_id].entries) == 0
    assert 'bra' not in index_uow.repo.indicies[
        create_resource.resource_id
    ].entries


def test_reindex_resource_command(
    search_unit_ctx: adapters.SearchUnitTestContext,
):
    create_entry_repo = lex_factories.CreateEntryRepositoryFactory()
    search_unit_ctx.command_bus.dispatch(create_entry_repo)
    create_resource = lex_factories.CreateResourceFactory(
        entry_repo_id=create_entry_repo.entity_id)
    search_unit_ctx.command_bus.dispatch(create_resource)
    create_entry = lex_factories.AddEntryFactory(
        resource_id=create_resource.resource_id,
        entry={'baseform': 'bra'},
    )
    search_unit_ctx.command_bus.dispatch(create_entry)

    reindex_resource = factories.ReindexResourceFactory(
        resource_id=create_resource.resource_id,
        version=1,
    )
    index_uow = search_unit_ctx.container.get(
        IndexUnitOfWork)
    previous_created_at = index_uow.repo.indicies[create_resource.resource_id].created_at
    search_unit_ctx.command_bus.dispatch(reindex_resource)

    index_uow = search_unit_ctx.container.get(IndexUnitOfWork)
    assert index_uow.was_committed

    assert index_uow.repo.indicies[create_resource.resource_id].created
    assert len(
        index_uow.repo.indicies[create_resource.resource_id].entries) == 1
    assert index_uow.repo.indicies[
        create_resource.resource_id
    ].created_at > previous_created_at

