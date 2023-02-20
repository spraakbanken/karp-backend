import logging  # noqa: D100, I001


from karp.foundation import events as foundation_events

from karp import command_bus
from karp.lex.domain import events as lex_events
from karp.lex.application.queries import EntryDto
from karp.search.application.queries import ResourceViews
from karp.search.application.repositories import IndexUnitOfWork
from karp.search.application.transformers import EntryTransformer, PreProcessor

from karp.lex.domain import events

from karp.search.domain import commands

logger = logging.getLogger(__name__)


class ReindexingResource(  # noqa: D101
    command_bus.CommandHandler[commands.ReindexResource]
):
    def __init__(  # noqa: D107
        self,
        index_uow: IndexUnitOfWork,
        resource_views: ResourceViews,
        pre_processor: PreProcessor,
    ) -> None:
        super().__init__()
        self.index_uow = index_uow
        self.resource_views = resource_views
        self.pre_processor = pre_processor

    def execute(self, command: commands.ReindexResource) -> None:  # noqa: D102
        logger.debug("Reindexing resource '%s'", command.resource_id)
        with self.index_uow as uw:
            uw.repo.create_index(
                command.resource_id,
                self.resource_views.get_resource_config(command.resource_id),
            )
            uw.repo.add_entries(
                command.resource_id, self.pre_processor.process(command.resource_id)
            )
            uw.commit()


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
        self, event: events.ResourceCreated, *args, **kwargs  # noqa: ANN002, ANN003
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
        self, event: events.ResourceDiscarded, *args, **kwargs  # noqa: ANN002, ANN003
    ):
        pass


class EntryAddedHandler(  # noqa: D101
    foundation_events.EventHandler[lex_events.EntryAdded]
):
    def __init__(  # noqa: D107, ANN204
        self,
        index_uow: IndexUnitOfWork,
        entry_transformer: EntryTransformer,
        resource_views: ResourceViews,
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
                    # entry_id=event.entry_id,
                    # repository_id=event.repo_id,
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
                # self.entry_transformer.update_references(resource_id, [event.entry_id])
            uw.commit()


class EntryUpdatedHandler(  # noqa: D101
    foundation_events.EventHandler[lex_events.EntryUpdated]
):
    def __init__(  # noqa: D107, ANN204
        self,
        index_uow: IndexUnitOfWork,
        entry_transformer: EntryTransformer,
        resource_views: ResourceViews,
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
                self.entry_transformer.update_references(resource_id, [event.id])
            uw.commit()
            # add_entries(event.resource_id, [entry], ctx)
            # ctx.index_uow.commit()


class EntryDeletedHandler(  # noqa: D101
    foundation_events.EventHandler[lex_events.EntryDeleted]
):
    def __init__(  # noqa: D107, ANN204
        self,
        index_uow: IndexUnitOfWork,
        entry_transformer: EntryTransformer,
        resource_views: ResourceViews,
    ):
        self.index_uow = index_uow
        self.entry_transformer = entry_transformer
        self.resource_views = resource_views

    def __call__(self, event: events.EntryDeleted):  # noqa: D102, ANN204
        with self.index_uow as uw:
            for resource_id in self.resource_views.get_resource_ids(event.repo_id):
                # uw.repo.delete_entry(resource_id, entry_id=event.entry_id)
                uw.repo.delete_entry(resource_id, entry_id=event.id)
                self.entry_transformer.update_references(resource_id, [event.id])
            uw.commit()
