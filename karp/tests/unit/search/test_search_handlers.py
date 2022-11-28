from typing import Callable

import pytest

from karp.lex.domain.events import ResourceCreated

from karp.search.application.repositories import IndexUnitOfWork
from karp.tests.unit.lex import factories as lex_factories
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
def test_index_reacts_on_lex_events(
    event_factory,
    predicate: Callable,
    search_unit_ctx: adapters.SearchUnitTestContext,
):
    resource_created = lex_factories.ResourceCreatedFactory()
    search_unit_ctx.event_bus.post(resource_created)  # type: ignore [arg-type]
    if event_factory:
        event = event_factory(resource_id=resource_created.resource_id)
        search_unit_ctx.event_bus.post(event)

    index_uow = search_unit_ctx.container.get(IndexUnitOfWork)  # type: ignore [misc]
    assert index_uow.was_committed  # type: ignore [attr-defined]

    assert predicate(index_uow.repo.indicies[resource_created.resource_id])  # type: ignore [attr-defined]


def test_index_reacts_on_entry_added_event(
    search_unit_ctx: adapters.SearchUnitTestContext,
):
    create_entry_repo = lex_factories.CreateEntryRepositoryFactory()
    search_unit_ctx.command_bus.dispatch(create_entry_repo)  # type: ignore [arg-type]
    create_resource = lex_factories.CreateResourceFactory(
        entry_repo_id=create_entry_repo.entity_id
    )
    search_unit_ctx.command_bus.dispatch(create_resource)  # type: ignore [arg-type]
    create_entry = lex_factories.AddEntryFactory(
        resource_id=create_resource.resource_id,
        entry={"baseform": "bra"},
    )
    search_unit_ctx.command_bus.dispatch(create_entry)  # type: ignore [arg-type]
    # if event_factory:
    #     event = event_factory(resource_id=create_resource.resource_id)
    #     search_unit_ctx.event_bus.post(event)

    index_uow = search_unit_ctx.container.get(IndexUnitOfWork)  # type: ignore [misc]
    assert index_uow.was_committed  # type: ignore [attr-defined]

    resource_index = index_uow.repo.indicies[create_resource.resource_id]  # type: ignore [attr-defined]
    assert resource_index.created
    assert len(resource_index.entries) == 1
    assert str(create_entry.entity_id) in resource_index.entries


def test_index_reacts_on_entry_updated_event(
    search_unit_ctx: adapters.SearchUnitTestContext,
):
    create_entry_repo = lex_factories.CreateEntryRepositoryFactory()
    search_unit_ctx.command_bus.dispatch(create_entry_repo)  # type: ignore [arg-type]
    create_resource = lex_factories.CreateResourceFactory(
        entry_repo_id=create_entry_repo.entity_id
    )
    search_unit_ctx.command_bus.dispatch(create_resource)  # type: ignore [arg-type]
    create_entry = lex_factories.AddEntryFactory(
        resource_id=create_resource.resource_id,
        entry={"baseform": "bra"},
    )
    search_unit_ctx.command_bus.dispatch(create_entry)  # type: ignore [arg-type]

    update_entry = lex_factories.UpdateEntryFactory(
        resource_id=create_resource.resource_id,
        entity_id=create_entry.entity_id,
        # entry_id="bra",
        entry={"baseform": "bra", "wordclass": "adjektiv"},
        version=1,
    )
    search_unit_ctx.command_bus.dispatch(update_entry)  # type: ignore [arg-type]

    index_uow = search_unit_ctx.container.get(IndexUnitOfWork)  # type: ignore [misc]
    assert index_uow.was_committed  # type: ignore [attr-defined]
    resource_index = index_uow.repo.indicies[create_resource.resource_id]  # type: ignore [attr-defined]
    assert resource_index.created
    assert len(resource_index.entries) == 1
    entry = resource_index.entries[str(update_entry.entity_id)]
    assert entry.entry["wordclass"] == "adjektiv"


def test_index_reacts_on_entry_deleted_event(
    search_unit_ctx: adapters.SearchUnitTestContext,
):
    create_entry_repo = lex_factories.CreateEntryRepositoryFactory()
    search_unit_ctx.command_bus.dispatch(create_entry_repo)  # type: ignore [arg-type]
    create_resource = lex_factories.CreateResourceFactory(
        entry_repo_id=create_entry_repo.entity_id
    )
    search_unit_ctx.command_bus.dispatch(create_resource)  # type: ignore [arg-type]
    create_entry = lex_factories.AddEntryFactory(
        resource_id=create_resource.resource_id,
        entry={"baseform": "bra"},
    )
    search_unit_ctx.command_bus.dispatch(create_entry)  # type: ignore [arg-type]

    delete_entry = lex_factories.DeleteEntryFactory(
        entity_id=create_entry.entity_id,
        resource_id=create_resource.resource_id,
        entry_id="bra",
        version=1,
    )
    search_unit_ctx.command_bus.dispatch(delete_entry)  # type: ignore [arg-type]

    index_uow = search_unit_ctx.container.get(IndexUnitOfWork)  # type: ignore [misc]
    assert index_uow.was_committed  # type: ignore [attr-defined]

    resource_index = index_uow.repo.indicies[create_resource.resource_id]  # type: ignore [attr-defined]
    assert resource_index.created
    assert len(resource_index.entries) == 0
    assert "bra" not in resource_index.entries


def test_reindex_resource_command(
    search_unit_ctx: adapters.SearchUnitTestContext,
):
    create_entry_repo = lex_factories.CreateEntryRepositoryFactory()
    search_unit_ctx.command_bus.dispatch(create_entry_repo)  # type: ignore [arg-type]
    create_resource = lex_factories.CreateResourceFactory(
        entry_repo_id=create_entry_repo.entity_id
    )
    search_unit_ctx.command_bus.dispatch(create_resource)  # type: ignore [arg-type]
    create_entry = lex_factories.AddEntryFactory(
        resource_id=create_resource.resource_id,
        entry={"baseform": "bra"},
    )
    search_unit_ctx.command_bus.dispatch(create_entry)  # type: ignore [arg-type]

    reindex_resource = factories.ReindexResourceFactory(
        resource_id=create_resource.resource_id,
        version=1,
    )
    index_uow = search_unit_ctx.container.get(IndexUnitOfWork)  # type: ignore [misc]
    resource_index = index_uow.repo.indicies[create_resource.resource_id]  # type: ignore [attr-defined]
    previous_created_at = resource_index.created_at

    search_unit_ctx.command_bus.dispatch(reindex_resource)  # type: ignore [arg-type]

    index_uow = search_unit_ctx.container.get(IndexUnitOfWork)  # type: ignore [misc]
    assert index_uow.was_committed  # type: ignore [attr-defined]

    assert resource_index.created
    assert len(resource_index.entries) == 1
    assert resource_index.created_at >= previous_created_at
