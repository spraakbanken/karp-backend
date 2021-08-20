import json
from karp.services import context

# from karp.infrastructure.unit_of_work import unit_of_work
import sys
import typing
from typing import Dict, List, Tuple, Optional
import collections
import logging

from karp.domain import events, model, errors, index, commands
from karp.domain.models.entry import Entry, create_entry
from karp.domain.models.resource import Resource
from karp.domain.repository import ResourceRepository
from karp.domain.index import IndexEntry, Index

from karp.services import context, network_handlers

# from karp.domain.services import network

# from .index import IndexModule
# import karp.resourcemgr as resourcemgr
# import karp.resourcemgr.entryread as entryread
# from karp.resourcemgr.resource import Resource
from karp import errors as karp_errors

# from karp.resourcemgr.entrymetadata import EntryMetadata

# indexer = IndexModule()

logger = logging.getLogger("karp")


# def pre_process_resource(
#     resource_obj: Resource,
# ) -> List[Tuple[str, EntryMetadata, Dict]]:
#     metadata = resourcemgr.get_all_metadata(resource_obj)
#     fields = resource_obj.config["fields"].items()
#     entries = resource_obj.model.query.filter_by(deleted=False)
#     return [
#         (
#             entry.entry_id,
#             metadata[entry.id],
#             transform_to_index_entry(resource_obj, json.loads(entry.body), fields),
#         )
#         for entry in entries
#     ]


def pre_process_resource(
    resource: Resource,
    resource_repo: ResourceRepository,
    indexer: Index,
) -> List[IndexEntry]:
    with unit_of_work(using=resource.entry_repository) as uw:
        index_entries = [
            transform_to_index_entry(resource_repo, indexer, resource, entry)
            for entry in uw.all_entries()
        ]
    return index_entries
    # metadata = resourcemgr.get_all_metadata(resource_obj)
    # fields = resource_obj.config["fields"].items()
    # entries = resource_obj.model.query.filter_by(deleted=False)
    # return [
    #     (
    #         entry.entry_id,
    #         metadata[entry.id],
    #         transform_to_index_entry(resource_obj, json.loads(entry.body), fields),
    #     )
    #     for entry in entries
    # ]


# def reindex(
#     resource_id: str,
#     version: Optional[int] = None,
#     search_entries: Optional[List[Tuple[str, EntryMetadata, Dict]]] = None,
# ) -> None:
#     """
#     If `search_entries` is not given, they will be fetched from DB and processed using `transform_to_index_entry`
#     If `search_entries` is given, they most have the same format as the output from `pre_process_resource`
#     """
#     resource_obj = resourcemgr.get_resource(resource_id, version=version)
#     try:
#         index_name = indexer.impl.create_index(resource_id, resource_obj.config)
#     except NotImplementedError:
#         _logger.error("No Index module is loaded. Check your configurations...")
#         sys.exit(errors.NoIndexModuleConfigured)
#     if not search_entries:
#         search_entries = pre_process_resource(resource_obj)
#     add_entries(index_name, search_entries, update_refs=False)
#     indexer.impl.publish_index(resource_id, index_name)
# def reindex(
#     indexer: Index,
#     resource_repo: ResourceRepository,
#     resource: Resource,
#     search_entries: Optional[List[IndexEntry]] = None,
# ):
def reindex_resource(cmd: commands.ReindexResource, ctx: context.Context):
    logger.debug("Reindexing resource '%s'", cmd.resource_id)
    with ctx.resource_uow as resource_uw:
        resource = resource_uw.resources.by_resource_id(cmd.resource_id)
        if not resource:
            raise errors.ResourceNotFound(resource_id=cmd.resource_id)


def reindex(
    evt: events.ResourcePublished,
    ctx: context.Context,
):
    print("creating index ...")
    index_name = indexer.create_index(resource.resource_id, resource.config)

    if not search_entries:
        print("preprocessing entries ...")
        search_entries = pre_process_resource(resource, resource_repo, indexer)
    print(f"adding entries to '{index_name}' ...")
    # add_entries(
    #     resource_repo,
    #     indexer,
    #     resource,
    #     search_entries,
    #     index_name=index_name,
    #     update_refs=False,
    # )
    indexer.add_entries(index_name, search_entries)
    print("publishing ...")
    indexer.publish_index(resource.resource_id, index_name)


# def publish_index(resource_id: str, version: Optional[int] = None) -> None:
def publish_index(
    evt: events.ResourcePublished,
    ctx: context.Context,
) -> None:
    print("calling reindex ...")
    # reindex(evt, ctx)
    with ctx.index_uow:
        ctx.index_uow.repo.publish_index(evt.resource_id)
        ctx.index_uow.commit()
    # if version:
    #     resourcemgr.publish_resource(resource_id, version)


def create_index(evt: events.ResourceCreated, ctx: context.Context):
    print(f"index_handlers.create_index: evt = {evt}")
    with ctx.index_uow:
        ctx.index_uow.repo.create_index(evt.resource_id, evt.config)
        ctx.index_uow.commit()


# def add_entries(
#     resource_id: str,
#     entries: List[Tuple[str, EntryMetadata, Dict]],
#     update_refs: bool = True,
# ) -> None:
#     indexer.impl.add_entries(resource_id, entries)
#     if update_refs:
#         _update_references(resource_id, [entry_id for (entry_id, _, _) in entries])


def add_entry(
    evt: events.EntryAdded,
    ctx: context.Context,
):
    with ctx.index_uow:
        entry = model.Entry(
            entity_id=evt.id,
            entry_id=evt.entry_id,
            resource_id=evt.resource_id,
            body=evt.body,
            message=evt.message,
            last_modified=evt.timestamp,
            last_modified_by=evt.user,
        )
        add_entries(evt.resource_id, [entry], ctx)
        ctx.index_uow.commit()


def update_entry(
    evt: events.EntryUpdated,
    ctx: context.Context,
):
    with ctx.index_uow:
        entry = model.Entry(
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
        ctx.index_uow.commit()

    # def add_entries(
    #     resource_repo: ResourceRepository,
    #     indexer: Index,
    #     resource: Resource,
    #     entries: List[Entry],
    #     *,
    #     update_refs: bool = True,
    #     index_name: Optional[str] = None,
    # ) -> None:


def add_entries(
    resource_id: str,
    entries: typing.List[model.Entry],
    ctx: context.Context,
    *,
    update_refs: bool = True,
    index_name: typing.Optional[str] = None,
):
    if not index_name:
        index_name = resource_id
    with ctx.index_uow:
        with ctx.resource_uow:
            resource = ctx.resource_uow.repo.by_resource_id(resource_id)
            if not resource:
                raise errors.ResourceNotFound(resource_id)
            ctx.index_uow.repo.add_entries(
                index_name,
                [transform_to_index_entry(resource, entry, ctx) for entry in entries],
            )
            if update_refs:
                _update_references(resource, entries, ctx)
            ctx.resource_uow.commit()
        ctx.index_uow.commit()


def delete_entry(evt: events.EntryDeleted, ctx: context.Context):
    with ctx.index_uow:
        ctx.index_uow.repo.delete_entry(evt.resource_id, entry_id=evt.entry_id)
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
        ctx.index_uow.commit()


def _update_references(
    # resource_id: str,
    # resource_repo: ResourceRepository,
    # indexer: Index,
    resource: model.Resource,
    entries: List[Entry],
    ctx: context.Context,
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
                    ref_index_entry = transform_to_index_entry(
                        # resource_repo,
                        # indexer,
                        ref_resource,
                        field_ref["entry"],
                        # ref_resource.config["fields"].items(),
                        ctx,
                    )
                    # metadata = resourcemgr.get_metadata(ref_resource, field_ref["id"])
                    add[ref_resource_id].append(ref_index_entry)

    for ref_resource_id, ref_entries in add.items():
        ctx.index_uow.repo.add_entries(ref_resource_id, ref_entries)


def transform_to_index_entry(
    # resource_id: str,
    # resource_repo: ResourceRepository,
    # indexer: Index,
    resource: model.Resource,
    src_entry: model.Entry,
    ctx: context.Context,
) -> index.IndexEntry:
    """
    TODO This is very slow (for resources with references) because of db-lookups everywhere in the code
    TODO We can pre-fetch the needed entries (same code that only looks for refs?) or
    TODO somehow get the needed entries in bulk after transforming some entries and insert them into
    TODO the transformed entries afterward. Very tricky.
    """
    print(f"transforming entry_id={src_entry.entry_id}")
    index_entry = ctx.index_uow.repo.create_empty_object()
    index_entry.id = src_entry.entry_id
    ctx.index_uow.repo.assign_field(index_entry, "_entry_version", src_entry.version)
    ctx.index_uow.repo.assign_field(
        index_entry, "_last_modified", src_entry.last_modified
    )
    ctx.index_uow.repo.assign_field(
        index_entry, "_last_modified_by", src_entry.last_modified_by
    )
    _transform_to_index_entry(
        resource,
        # resource_repo,
        # indexer,
        src_entry.body,
        index_entry,
        resource.config["fields"].items(),
        ctx,
    )
    return index_entry


def _evaluate_function(
    # resource_repo: ResourceRepository,
    # indexer: Index,
    function_conf: typing.Dict,
    src_entry: typing.Dict,
    src_resource: model.Resource,
    ctx: context.Context,
):
    print(f"indexing._evaluate_function src_resource={src_resource.resource_id}")
    print(f"indexing._evaluate_function src_entry={src_entry}")
    if "multi_ref" in function_conf:
        function_conf = function_conf["multi_ref"]
        target_field = function_conf["field"]
        if "resource_id" in function_conf:
            print(
                f"indexing._evaluate_function: trying to find '{function_conf['resource_id']}'"
            )
            target_resource = ctx.resource_uow.repo.by_resource_id(
                function_conf["resource_id"], version=function_conf["resource_version"]
            )
            if target_resource is None:
                logger.warning(
                    "Didn't find the resource with resource_id='%s'",
                    function_conf["resource_id"],
                )
                return ctx.index_uow.repo.create_empty_list()
        else:
            target_resource = src_resource
        print(
            f"indexing._evaluate_function target_resource={target_resource.resource_id}"
        )
        if "test" in function_conf:
            operator, args = list(function_conf["test"].items())[0]
            if operator in ["equals", "contains"]:
                filters = {"discarded": False}
                for arg in args:
                    if "self" in arg:
                        filters[target_field] = src_entry[arg["self"]]
                    else:
                        raise NotImplementedError()
                # target_entries = entryread.get_entries_by_column(
                #     target_resource, filters
                # )
                with ctx.entry_uows.get(
                    target_resource.resource_id
                ) as target_entries_uw:
                    target_entries = target_entries_uw.repo.by_referenceable(filters)
            else:
                raise NotImplementedError()
        else:
            raise NotImplementedError()

        res = ctx.index_uow.repo.create_empty_list()
        for entry in target_entries:
            index_entry = ctx.index_uow.repo.create_empty_object()
            list_of_sub_fields = (("tmp", function_conf["result"]),)
            _transform_to_index_entry(
                target_resource,
                # resource_repo,
                # indexer,
                {"tmp": entry.body},
                index_entry,
                list_of_sub_fields,
                ctx,
            )
            ctx.index_uow.repo.add_to_list_field(res, index_entry.entry["tmp"])
    elif "plugin" in function_conf:
        plugin_id = function_conf["plugin"]
        import karp.pluginmanager as plugins

        res = plugins.plugins[plugin_id].apply_plugin_function(
            src_resource.id, src_resource.version, src_entry
        )
    else:
        raise NotImplementedError()
    return res


def _transform_to_index_entry(
    resource: model.Resource,
    # resource_repo: ResourceRepository,
    # indexer: Index,
    _src_entry: typing.Dict,
    _index_entry: index.IndexEntry,
    fields,
    ctx: context.Context,
):
    for field_name, field_conf in fields:
        if field_conf.get("virtual"):
            print("found virtual field")
            res = _evaluate_function(field_conf["function"], _src_entry, resource, ctx)
            print(f"res = {res}")
            if res:
                ctx.index_uow.repo.assign_field(_index_entry, "v_" + field_name, res)
        elif field_conf.get("ref"):
            ref_field = field_conf["ref"]
            if ref_field.get("resource_id"):
                ref_resource = ctx.resource_uow.repo.by_resource_id(
                    ref_field["resource_id"], version=ref_field["resource_version"]
                )
                # if not ref_resource:
                #     raise errors.ResourceNotFoundError(
                #         ref_field["resource_id"], ref_field["resource_version"]
                #     )
                if ref_field["field"].get("collection"):
                    ref_objs = []
                    if ref_resource:
                        for ref_id in _src_entry[field_name]:
                            with ctx.entry_uows.get(
                                ref_resource.resource_id
                            ) as ref_resource_entries_uw:
                                ref_entry_body = (
                                    ref_resource_entries_uw.repo.by_entry_id(
                                        str(ref_id)
                                    )
                                )
                                ref_resource_entries_uw.commit()
                            if ref_entry_body:
                                ref_entry = {field_name: ref_entry_body.body}
                                ref_index_entry = (
                                    ctx.index_uow.repo.create_empty_object()
                                )
                                list_of_sub_fields = ((field_name, ref_field["field"]),)
                                _transform_to_index_entry(
                                    resource,
                                    # resource_repo,
                                    # indexer,
                                    ref_entry,
                                    ref_index_entry,
                                    list_of_sub_fields,
                                    ctx,
                                )
                                ref_objs.append(ref_index_entry.entry[field_name])
                    ctx.index_uow.repo.assign_field(
                        _index_entry, "v_" + field_name, ref_objs
                    )
                else:
                    raise NotImplementedError()
            else:
                ref_id = _src_entry.get(field_name)
                if not ref_id:
                    continue
                if not ref_field["field"].get("collection", False):
                    ref_id = [ref_id]

                for elem in ref_id:
                    with ctx.entry_uows.get(
                        resource.resource_id
                    ) as resource_entries_uw:
                        ref = resource_entries_uw.repo.by_entry_id(str(elem))
                        resource_entries_uw.commit()
                    if ref:
                        ref_entry = {field_name: ref.body}
                        ref_index_entry = ctx.index_uow.repo.create_empty_object()
                        list_of_sub_fields = ((field_name, ref_field["field"]),)
                        _transform_to_index_entry(
                            resource,
                            # resource_repo,
                            # indexer,
                            ref_entry,
                            ref_index_entry,
                            list_of_sub_fields,
                            ctx,
                        )
                        ctx.index_uow.repo.assign_field(
                            _index_entry,
                            "v_" + field_name,
                            ref_index_entry.entry[field_name],
                        )

        if field_conf["type"] == "object":
            print("found field with type 'object'")
            field_content = ctx.index_uow.repo.create_empty_object()
            if field_name in _src_entry:
                _transform_to_index_entry(
                    resource,
                    # resource_repo,
                    # indexer,
                    _src_entry[field_name],
                    field_content,
                    field_conf["fields"].items(),
                    ctx,
                )
        else:
            field_content = _src_entry.get(field_name)

        if field_content:
            ctx.index_uow.repo.assign_field(_index_entry, field_name, field_content)
