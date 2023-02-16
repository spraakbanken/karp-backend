import logging  # noqa: D100, I001

from typing import Iterable

from karp.foundation import events as foundation_events

from karp import command_bus
from karp.lex.domain import events as lex_events
from karp.lex.application.queries import EntryDto
from karp.search.application.queries import ResourceViews
from karp.search.application.repositories import IndexUnitOfWork
from karp.search.application.transformers import EntryTransformer, PreProcessor

from karp.lex.domain import events

# , errors, events, search_service, model
from karp.search.domain import commands

logger = logging.getLogger(__name__)


# def pre_process_resource(
#     resource_obj: Resource,
# ) -> List[Tuple[str, EntryMetadata, Dict]]:
#     metadata = resourcemgr.get_all_metadata(resource_obj)
#     fields = resource_obj.config["fields"].items()
#     entries = resource_obj.entities.query.filter_by(deleted=False)
#     return [
#         (
#             entry.entry_id,
#             metadata[entry.id],
#             transform_to_search_service_entry(resource_obj, json.loads(entry.body), fields),
#         )
#         for entry in entries
#     ]

# metadata = resourcemgr.get_all_metadata(resource_obj)
# fields = resource_obj.config["fields"].items()
# entries = resource_obj.entities.query.filter_by(deleted=False)
# return [
#     (
#         entry.entry_id,
#         metadata[entry.id],
#         transform_to_search_service_entry(resource_obj, json.loads(entry.body), fields),
#     )
#     for entry in entries
# ]


# def research_service(
#     resource_id: str,
#     version: Optional[int] = None,
#     search_entries: Optional[List[Tuple[str, EntryMetadata, Dict]]] = None,
# ) -> None:
#     """
#     If `search_entries` is not given, they will be fetched from DB and processed using `transform_to_search_service_entry`
#     If `search_entries` is given, they most have the same format as the output from `pre_process_resource`
#     """
#     resource_obj = resourcemgr.get_resource(resource_id, version=version)
#     try:
#         search_service_name = search_serviceer.impl.create_search_service(resource_id, resource_obj.config)
#     except NotImplementedError:
#         _logger.error("No SearchService module is loaded. Check your configurations...")
#         sys.exit(errors.NoSearchServiceModuleConfigured)
#     if not search_entries:
#         search_entries = pre_process_resource(resource_obj)
#     add_entries(search_service_name, search_entries, update_refs=False)
#     search_serviceer.impl.publish_search_service(resource_id, search_service_name)
# def research_service(
#     search_serviceer: SearchService,
#     resource_repo: ResourceRepository,
#     resource: Resource,
#     search_entries: Optional[List[IndexEntry]] = None,
# ):


class ReindexingResource(command_bus.CommandHandler[commands.ReindexResource]):  # noqa: D101
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

    def collect_new_events(self) -> Iterable[foundation_events.Event]:  # noqa: D102
        yield from self.index_uow.collect_new_events()

    def __call__(self, event: events.ResourceCreated, *args, **kwargs):  # noqa: ANN003, ANN204, ANN002, D102
        with self.index_uow as uw:
            uw.repo.create_index(event.resource_id, event.config)
            uw.commit()


class DeletingIndex(foundation_events.EventHandler[lex_events.ResourceDiscarded]):  # noqa: D101
    def __init__(self, index_uow: IndexUnitOfWork):  # noqa: D107, ANN204
        self.index_uow = index_uow

    def collect_new_events(self) -> Iterable[foundation_events.Event]:  # noqa: D102
        yield from self.index_uow.collect_new_events()

    def __call__(self, event: events.ResourceDiscarded, *args, **kwargs):  # noqa: ANN003, ANN204, ANN002, D102
        pass


# def add_entries(
#     resource_id: str,
#     entries: List[Tuple[str, EntryMetadata, Dict]],
#     update_refs: bool = True,
# ) -> None:
#     search_serviceer.impl.add_entries(resource_id, entries)
#     if update_refs:
#         _update_references(resource_id, [entry_id for (entry_id, _, _) in entries])


class EntryAddedHandler(foundation_events.EventHandler[lex_events.EntryAdded]):  # noqa: D101
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
                    entity_id=event.entity_id,
                    # entry_id=event.entry_id,
                    repository_id=event.repo_id,
                    resource=resource_id,
                    entry=event.body,
                    message=event.message,
                    last_modified=event.timestamp,
                    last_modified_by=event.user,
                    version=1,
                )
                uw.repo.add_entries(
                    resource_id, [self.entry_transformer.transform(resource_id, entry)]
                )
                # self.entry_transformer.update_references(resource_id, [event.entry_id])
            uw.commit()


class EntryUpdatedHandler(foundation_events.EventHandler[lex_events.EntryUpdated]):  # noqa: D101
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
                    entity_id=event.entity_id,
                    # entry_id=event.entry_id,
                    repository_id=event.repo_id,
                    resource=resource_id,
                    entry=event.body,
                    message=event.message,
                    last_modified=event.timestamp,
                    last_modified_by=event.user,
                    version=event.version,
                )
                uw.repo.add_entries(
                    resource_id, [self.entry_transformer.transform(resource_id, entry)]
                )
                self.entry_transformer.update_references(resource_id, [event.entity_id])
            uw.commit()
            # add_entries(event.resource_id, [entry], ctx)
            # ctx.index_uow.commit()


class EntryDeletedHandler(foundation_events.EventHandler[lex_events.EntryDeleted]):  # noqa: D101
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
                uw.repo.delete_entry(resource_id, entry_id=event.entity_id)
                self.entry_transformer.update_references(resource_id, [event.entity_id])
            uw.commit()
