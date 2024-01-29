import logging  # noqa: D100, I001


from karp.foundation import events as foundation_events

from karp.lex.domain import events as lex_events
from karp.lex.application.queries import EntryDto
from karp.search.application.repositories import IndexUnitOfWork

from karp.lex.domain import events

from karp.search.generic_resources import GenericResourceViews
from karp.search_infrastructure.transformers.generic_entry_transformer import (
    GenericEntryTransformer,
)

logger = logging.getLogger(__name__)


class ResourcePublishedHandler(  # noqa: D101
    foundation_events.EventHandler[lex_events.ResourcePublished]
):
    def __init__(self, index_uow: IndexUnitOfWork):  # noqa: D107, ANN204
        self.index_uow = index_uow

    def __call__(  # noqa: D102
        self,
        event: events.ResourcePublished,
        *args,  # noqa: ANN002
        **kwargs,  # noqa: ANN003
    ) -> None:
        # research_service(event, ctx)
        with self.index_uow as uw:
            uw.repo.publish_index(event.resource_id)
            uw.commit()
        # if version:
        #     resourcemgr.publish_resource(resource_id, version)


class CreateSearchServiceHandler(  # noqa: D101
    foundation_events.EventHandler[lex_events.ResourceCreated]
):
    def __init__(self, index_uow: IndexUnitOfWork):  # noqa: D107, ANN204
        self.index_uow = index_uow

    def __call__(  # noqa: D102, ANN204
        self,
        event: events.ResourceCreated,
        *args,
        **kwargs,  # noqa: ANN002, ANN003
    ):
        print(f"{event.resource_id=}")
        with self.index_uow as uw:
            uw.repo.create_index(event.resource_id, event.config)
            uw.commit()


class DeletingIndex(  # noqa: D101
    foundation_events.EventHandler[lex_events.ResourceDiscarded]
):
    def __init__(self, index_uow: IndexUnitOfWork):  # noqa: D107, ANN204
        self.index_uow = index_uow

    def __call__(  # noqa: D102, ANN204
        self,
        event: events.ResourceDiscarded,
        *args,
        **kwargs,  # noqa: ANN002, ANN003
    ):
        print(f"{event.resource_id=}")

        with self.index_uow as uw:
            uw.repo.delete_index(event.resource_id)
            uw.commit()


class EntryAddedHandler(  # noqa: D101
    foundation_events.EventHandler[lex_events.EntryAdded]
):
    def __init__(  # noqa: D107, ANN204
        self,
        index_uow: IndexUnitOfWork,
        entry_transformer: GenericEntryTransformer,
        resource_views: GenericResourceViews,
    ):
        self.index_uow = index_uow
        self.entry_transformer = entry_transformer
        self.resource_views = resource_views

    def __call__(  # noqa: D102, ANN204
        self,
        event: events.EntryAdded,
        *args,  # noqa: ANN002
        **kwargs,  # noqa: ANN003
    ):
        with self.index_uow as uw:
            for resource_id in self.resource_views.get_resource_ids(event.repo_id):
                entry = EntryDto(
                    id=event.id,
                    resource=resource_id,
                    entry=event.body,
                    message=event.message,
                    lastModified=event.timestamp,
                    lastModifiedBy=event.user,
                    version=1,
                )
                uw.repo.add_entries(
                    resource_id, [self.entry_transformer.transform(resource_id, entry)]
                )
            uw.commit()


class EntryUpdatedHandler(  # noqa: D101
    foundation_events.EventHandler[lex_events.EntryUpdated]
):
    def __init__(  # noqa: D107, ANN204
        self,
        index_uow: IndexUnitOfWork,
        entry_transformer: GenericEntryTransformer,
        resource_views: GenericResourceViews,
    ):
        self.index_uow = index_uow
        self.entry_transformer = entry_transformer
        self.resource_views = resource_views

    def __call__(  # noqa: D102, ANN204
        self,
        event: events.EntryUpdated,
        *args,  # noqa: ANN002
        **kwargs,  # noqa: ANN003
    ):
        with self.index_uow as uw:
            for resource_id in self.resource_views.get_resource_ids(event.repo_id):
                entry = EntryDto(
                    id=event.id,
                    # repository_id=event.repo_id,
                    resource=resource_id,
                    entry=event.body,
                    message=event.message,
                    lastModified=event.timestamp,
                    lastModifiedBy=event.user,
                    version=event.version,
                )
                uw.repo.add_entries(
                    resource_id, [self.entry_transformer.transform(resource_id, entry)]
                )
            uw.commit()


class EntryDeletedHandler(  # noqa: D101
    foundation_events.EventHandler[lex_events.EntryDeleted]
):
    def __init__(  # noqa: D107, ANN204
        self,
        index_uow: IndexUnitOfWork,
        entry_transformer: GenericEntryTransformer,
        resource_views: GenericResourceViews,
    ):
        self.index_uow = index_uow
        self.entry_transformer = entry_transformer
        self.resource_views = resource_views

    def __call__(self, event: events.EntryDeleted):  # noqa: D102, ANN204
        with self.index_uow as uw:
            for resource_id in self.resource_views.get_resource_ids(event.repo_id):
                uw.repo.delete_entry(resource_id, entry_id=event.id)
            uw.commit()
