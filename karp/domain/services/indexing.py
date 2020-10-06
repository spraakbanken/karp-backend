import json
import sys
from typing import Dict, List, Tuple, Optional
import collections
import logging

from .index import IndexModule
import karp.resourcemgr as resourcemgr
import karp.resourcemgr.entryread as entryread
import karp.network as network
from karp.resourcemgr.resource import Resource
from karp import errors
from karp.resourcemgr.entrymetadata import EntryMetadata

indexer = IndexModule()

_logger = logging.getLogger("karp")


def pre_process_resource(
    resource_obj: Resource,
) -> List[Tuple[str, EntryMetadata, Dict]]:
    metadata = resourcemgr.get_all_metadata(resource_obj)
    fields = resource_obj.config["fields"].items()
    entries = resource_obj.model.query.filter_by(deleted=False)
    return [
        (
            entry.entry_id,
            metadata[entry.id],
            transform_to_index_entry(resource_obj, json.loads(entry.body), fields),
        )
        for entry in entries
    ]


def reindex(
    resource_id: str,
    version: Optional[int] = None,
    search_entries: Optional[List[Tuple[str, EntryMetadata, Dict]]] = None,
) -> None:
    """
    If `search_entries` is not given, they will be fetched from DB and processed using `transform_to_index_entry`
    If `search_entries` is given, they most have the same format as the output from `pre_process_resource`
    """
    resource_obj = resourcemgr.get_resource(resource_id, version=version)
    try:
        index_name = indexer.impl.create_index(resource_id, resource_obj.config)
    except NotImplementedError:
        _logger.error("No Index module is loaded. Check your configurations...")
        sys.exit(errors.NoIndexModuleConfigured)
    if not search_entries:
        search_entries = pre_process_resource(resource_obj)
    add_entries(index_name, search_entries, update_refs=False)
    indexer.impl.publish_index(resource_id, index_name)


def publish_index(resource_id: str, version: Optional[int] = None) -> None:
    reindex(resource_id, version=version)
    if version:
        resourcemgr.publish_resource(resource_id, version)


def add_entries(
    resource_id: str,
    entries: List[Tuple[str, EntryMetadata, Dict]],
    update_refs: bool = True,
) -> None:
    indexer.impl.add_entries(resource_id, entries)
    if update_refs:
        _update_references(resource_id, [entry_id for (entry_id, _, _) in entries])


def delete_entry(resource_id: str, entry_id: str) -> None:
    indexer.impl.delete_entry(resource_id, entry_id)
    _update_references(resource_id, [entry_id])


def _update_references(resource_id: str, entry_ids: List[str]) -> None:
    add = collections.defaultdict(list)
    for src_entry_id in entry_ids:
        refs = network.get_referenced_entries(resource_id, None, src_entry_id)
        for field_ref in refs:
            ref_resource_id = field_ref["resource_id"]
            ref_resource = resourcemgr.get_resource(
                ref_resource_id, version=(field_ref["resource_version"])
            )
            body = transform_to_index_entry(
                ref_resource, field_ref["entry"], ref_resource.config["fields"].items()
            )
            metadata = resourcemgr.get_metadata(ref_resource, field_ref["id"])
            add[ref_resource_id].append(((field_ref["entry_id"]), metadata, body))
    for ref_resource_id, ref_entries in add.items():
        indexer.impl.add_entries(ref_resource_id, ref_entries)


def transform_to_index_entry(
    resource: resourcemgr.Resource, src_entry: Dict, fields: Tuple[str, Dict]
):
    """
    TODO This is very slow (for resources with references) because of db-lookups everywhere in the code
    TODO We can pre-fetch the needed entries (same code that only looks for refs?) or
    TODO somehow get the needed entries in bulk after transforming some entries and insert them into
    TODO the transformed entries afterward. Very tricky.
    """
    index_entry = indexer.impl.create_empty_object()
    _transform_to_index_entry(resource, src_entry, index_entry, fields)
    return index_entry


def _evaluate_function(
    function_conf: Dict, src_entry: Dict, src_resource: resourcemgr.Resource
):
    if "multi_ref" in function_conf:
        function_conf = function_conf["multi_ref"]
        target_field = function_conf["field"]
        if "resource_id" in function_conf:
            target_resource = resourcemgr.get_resource(
                function_conf["resource_id"], function_conf["resource_version"]
            )
        else:
            target_resource = src_resource

        if "test" in function_conf:
            operator, args = list(function_conf["test"].items())[0]
            filters = {"deleted": False}
            if operator == "equals":
                for arg in args:
                    if "self" in arg:
                        filters[target_field] = src_entry[arg["self"]]
                    else:
                        raise NotImplementedError()
                target_entries = entryread.get_entries_by_column(
                    target_resource, filters
                )
            elif operator == "contains":
                for arg in args:
                    if "self" in arg:
                        filters[target_field] = src_entry[arg["self"]]
                    else:
                        raise NotImplementedError()
                target_entries = entryread.get_entries_by_column(
                    target_resource, filters
                )
            else:
                raise NotImplementedError()
        else:
            raise NotImplementedError()

        res = indexer.impl.create_empty_list()
        for entry in target_entries:
            index_entry = indexer.impl.create_empty_object()
            list_of_sub_fields = (("tmp", function_conf["result"]),)
            _transform_to_index_entry(
                target_resource,
                {"tmp": entry["entry"]},
                index_entry,
                list_of_sub_fields,
            )
            indexer.impl.add_to_list_field(res, index_entry["tmp"])
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
    resource: resourcemgr.Resource, _src_entry: Dict, _index_entry, fields
):
    for field_name, field_conf in fields:
        if field_conf.get("virtual", False):
            res = _evaluate_function(field_conf["function"], _src_entry, resource)
            if res:
                indexer.impl.assign_field(_index_entry, "v_" + field_name, res)
        elif field_conf.get("ref", {}):
            ref_field = field_conf["ref"]
            if ref_field.get("resource_id"):
                ref_resource = resourcemgr.get_resource(
                    ref_field["resource_id"], version=ref_field["resource_version"]
                )
                if ref_field["field"].get("collection"):
                    ref_objs = []
                    for ref_id in _src_entry[field_name]:
                        ref_entry_body = entryread.get_entry_by_entry_id(
                            ref_resource, str(ref_id)
                        )
                        if ref_entry_body:
                            ref_entry = {field_name: json.loads(ref_entry_body.body)}
                            ref_index_entry = {}
                            list_of_sub_fields = ((field_name, ref_field["field"]),)
                            _transform_to_index_entry(
                                resource, ref_entry, ref_index_entry, list_of_sub_fields
                            )
                            ref_objs.append(ref_index_entry[field_name])
                    indexer.impl.assign_field(_index_entry, "v_" + field_name, ref_objs)
                else:
                    raise NotImplementedError()
            else:
                ref_id = _src_entry.get(field_name)
                if not ref_id:
                    continue
                if not ref_field["field"].get("collection", False):
                    ref_id = [ref_id]

                for elem in ref_id:
                    ref = entryread.get_entry_by_entry_id(resource, str(elem))
                    if ref:
                        ref_entry = {field_name: json.loads(ref.body)}
                        ref_index_entry = {}
                        list_of_sub_fields = ((field_name, ref_field["field"]),)
                        _transform_to_index_entry(
                            resource, ref_entry, ref_index_entry, list_of_sub_fields
                        )
                        indexer.impl.assign_field(
                            _index_entry, "v_" + field_name, ref_index_entry[field_name]
                        )

        if field_conf["type"] == "object":
            field_content = indexer.impl.create_empty_object()
            if field_name in _src_entry:
                _transform_to_index_entry(
                    resource,
                    _src_entry[field_name],
                    field_content,
                    field_conf["fields"].items(),
                )
        else:
            field_content = _src_entry.get(field_name)

        if field_content:
            indexer.impl.assign_field(_index_entry, field_name, field_content)
