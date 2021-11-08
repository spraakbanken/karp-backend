import collections
import json
import logging
# from karp.infrastructure.unit_of_work import unit_of_work
import sys
import typing
from typing import Dict, List, Optional, Tuple, Iterable

from karp.foundation import messagebus, events as foundation_events
from karp.lex.domain import events as lex_events
from karp.search.application.repositories import SearchServiceUnitOfWork
from karp.search.application.transformers import EntryTransformer
# from .search_service import SearchServiceModule
# import karp.resourcemgr as resourcemgr
# import karp.resourcemgr.entryread as entryread
# from karp.resourcemgr.resource import Resource
from karp import errors as karp_errors
from karp.lex.domain import events, entities
# , errors, events, search_service, model
from karp.search.domain import commands, search_service
from karp.search.domain.search_service import SearchService, IndexEntry
from karp.lex.domain.entities.entry import Entry, create_entry
# from karp.domain.models.resource import Resource
# from karp.domain.repository import ResourceRepository
# from karp.services import context, network_handlers

# from karp.domain.services import network


# from karp.resourcemgr.entrymetadata import EntryMetadata

# search_serviceer = SearchServiceModule()

logger = logging.getLogger("karp")


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


def pre_process_resource(
    resource_id: str,
) -> typing.Iterable[IndexEntry]:
    with ctx.resource_uow as uw:
        resource = uw.repo.by_resource_id(resource_id)
        if not resource:
            raise errors.ResourceNotFound(resource_id=resource_id)

    with ctx.entry_uows.get(resource_id) as uw:
        for entry in uw.repo.all_entries():
            yield transform_to_search_service_entry(resource, entry, ctx)

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


def research_service_resource(cmd: commands.ReindexResource):
    logger.debug("Reindexing resource '%s'", cmd.resource_id)
    with ctx.resource_uow as resource_uw:
        resource = resource_uw.resources.by_resource_id(cmd.resource_id)
        if not resource:
            raise errors.ResourceNotFound(resource_id=cmd.resource_id)
    with ctx.search_service_uow as search_service_uw:
        search_service_uw.repo.create_search_service(
            cmd.resource_id, resource.config)
        search_service_uw.repo.add_entries(
            cmd.resource_id, pre_process_resource(cmd.resource_id, ctx)
        )
        search_service_uw.commit()


def research_service(
    evt: events.ResourcePublished,
):
    print("creating search_service ...")
    search_service_name = search_serviceer.create_search_service(
        resource.resource_id, resource.config)

    if not search_entries:
        print("preprocessing entries ...")
        search_entries = pre_process_resource(
            resource, resource_repo, search_serviceer)
    print(f"adding entries to '{search_service_name}' ...")
    # add_entries(
    #     resource_repo,
    #     search_serviceer,
    #     resource,
    #     search_entries,
    #     search_service_name=search_service_name,
    #     update_refs=False,
    # )
    search_serviceer.add_entries(search_service_name, search_entries)
    print("publishing ...")
    search_serviceer.publish_search_service(
        resource.resource_id, search_service_name)


# def publish_search_service(resource_id: str, version: Optional[int] = None) -> None:
class ResourcePublishedHandler(foundation_events.EventHandler[lex_events.ResourcePublished]):
    def __init__(
        self,
        search_service_uow: SearchServiceUnitOfWork
    ):
        self.search_service_uow = search_service_uow

    def __call__(
        self,
        evt: events.ResourcePublished,
    ) -> None:
        print("calling research_service ...")
        # research_service(evt, ctx)
        with self.search_service_uow as uw:
            uw.repo.publish_index(evt.resource_id)
            uw.commit()
        # if version:
        #     resourcemgr.publish_resource(resource_id, version)


class CreateSearchServiceHandler(foundation_events.EventHandler[lex_events.ResourceCreated]):
    def __init__(
        self,
        search_service_uow: SearchServiceUnitOfWork
    ):
        self.search_service_uow = search_service_uow

    def collect_new_events(self) -> Iterable[foundation_events.Event]:
        yield from self.search_service_uow.collect_new_events()

    def __call__(self, evt: events.ResourceCreated):
        print(f"search_service_handlers.create_search_service: evt = {evt}")
        with self.search_service_uow as uw:
            uw.repo.create_index(evt.resource_id, evt.config)
            uw.commit()


# def add_entries(
#     resource_id: str,
#     entries: List[Tuple[str, EntryMetadata, Dict]],
#     update_refs: bool = True,
# ) -> None:
#     search_serviceer.impl.add_entries(resource_id, entries)
#     if update_refs:
#         _update_references(resource_id, [entry_id for (entry_id, _, _) in entries])


class EntryAddedHandler(foundation_events.EventHandler[lex_events.EntryAdded]):
    def __init__(
        self,
        search_service_uow: SearchServiceUnitOfWork,
        entry_transformer: EntryTransformer,
    ):
        self.search_service_uow = search_service_uow
        self.entry_transformer = entry_transformer

    def __call__(
        self,
        evt: events.EntryAdded,
    ):
        with self.search_service_uow as uw:
            entry = entities.Entry(
                entity_id=evt.id,
                entry_id=evt.entry_id,
                resource_id=evt.resource_id,
                body=evt.body,
                message=evt.message,
                last_modified=evt.timestamp,
                last_modified_by=evt.user,
            )
            uw.repo.add_entries(
                evt.resource_id,
                [self.entry_transformer.transform(evt.resource_id, entry)]
            )
            uw.commit()


def update_entry(
    evt: events.EntryUpdated,
):
    with ctx.search_service_uow:
        entry = entities.Entry(
            entity_id=evt.id,
            entry_id=evt.entry_id,
            resource_id=evt.resource_id,
            body=evt.body,
            message=evt.message,
            last_modified=evt.timestamp,
            last_modified_by=evt.user,
            version=evt.version,
        )
        add_entries(evt.resource_id, [entry], ctx)
        ctx.search_service_uow.commit()

    # def add_entries(
    #     resource_repo: ResourceRepository,
    #     search_serviceer: SearchService,
    #     resource: Resource,
    #     entries: List[Entry],
    #     *,
    #     update_refs: bool = True,
    #     search_service_name: Optional[str] = None,
    # ) -> None:


def add_entries(
    resource_id: str,
    entries: typing.List[entities.Entry],
    *,
    update_refs: bool = True,
    search_service_name: typing.Optional[str] = None,
):
    if not search_service_name:
        search_service_name = resource_id
    with ctx.search_service_uow:
        with ctx.resource_uow:
            resource = ctx.resource_uow.repo.by_resource_id(resource_id)
            if not resource:
                raise errors.ResourceNotFound(resource_id)
            ctx.search_service_uow.repo.add_entries(
                search_service_name,
                [transform_to_search_service_entry(resource, entry, ctx)
                 for entry in entries],
            )
            if update_refs:
                _update_references(resource, entries, ctx)
            ctx.resource_uow.commit()
        ctx.search_service_uow.commit()


def delete_entry(evt: events.EntryDeleted):
    with ctx.search_service_uow:
        ctx.search_service_uow.repo.delete_entry(
            evt.resource_id, entry_id=evt.entry_id)
        with ctx.resource_uow:
            resource = ctx.resource_uow.repo.by_resource_id(evt.resource_id)
            if not resource:
                raise errors.ResourceNotFound(evt.resource_id)
            with ctx.entry_uows.get(evt.resource_id) as uow:
                entry = uow.repo.by_entry_id(evt.entry_id)
                if not entry:
                    raise errors.EntryNotFound(evt.entry_id, evt.resource_id)
                _update_references(resource, [entry], ctx)
                uow.commit()
            ctx.resource_uow.commit()
        ctx.search_service_uow.commit()


def _update_references(
    # resource_id: str,
    # resource_repo: ResourceRepository,
    # search_serviceer: SearchService,
    resource: entities.Resource,
    entries: List[Entry],
) -> None:
    add = collections.defaultdict(list)
    with ctx.resource_uow:
        for src_entry in entries:
            refs = network_handlers.get_referenced_entries(
                resource, None, src_entry.entry_id, ctx
            )
            for field_ref in refs:
                ref_resource_id = field_ref["resource_id"]
                ref_resource = ctx.resource_uow.repo.by_resource_id(
                    ref_resource_id, version=(field_ref["resource_version"])
                )
                if ref_resource:
                    ref_search_service_entry = transform_to_search_service_entry(
                        # resource_repo,
                        # search_serviceer,
                        ref_resource,
                        field_ref["entry"],
                        # ref_resource.config["fields"].items(),
                        ctx,
                    )
                    # metadata = resourcemgr.get_metadata(ref_resource, field_ref["id"])
                    add[ref_resource_id].append(ref_search_service_entry)

    for ref_resource_id, ref_entries in add.items():
        ctx.search_service_uow.repo.add_entries(ref_resource_id, ref_entries)
