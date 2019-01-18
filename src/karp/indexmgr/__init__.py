import json
from typing import Dict

from .index import IndexModule
import karp.resourcemgr as resourcemgr
import karp.resourcemgr.entryread as entryread

indexer = IndexModule()


def reindex(resource_id, index_name, version=None):
    resource_obj = resourcemgr.get_resource(resource_id, version=version)
    entries = resource_obj.model.query.filter_by(deleted=False)

    def prepare_entries():
        fields = resource_obj.config['fields'].items()
        for entry in entries:
            yield (entry.entry_id, transform_to_index_entry(resource_obj, json.loads(entry.body), fields))

    add_entries(index_name, prepare_entries(), do_reindex=False)


def create_index(resource_id, version=None):
    resource = resourcemgr.get_resource(resource_id, version=version)
    return indexer.impl.create_index(resource_id, resource.config)


def publish_index(alias_name, index_name):
    return indexer.impl.publish_index(alias_name, index_name)


def add_entries(resource_id, src_entries, do_reindex=True):
    """
    Tmp solution to changes in entries that are referred to by another entry (we don't know yet!):
      Reindex after every change...
    """
    if do_reindex:
        index_name = create_index(resource_id)
        reindex(resource_id, index_name)
        publish_index(resource_id, index_name)
    else:
        indexer.impl.add_entries(resource_id, src_entries)


def delete_entry(resource_id, entry_id):
    """
    Tmp solution to changes in entries that are referred to by another entry (we don't know yet!):
      Reindex after every change...
      For delete this currently means "do nothing", since the deleted element will not be included on next reindex
    """
    index_name = create_index(resource_id)
    reindex(resource_id, index_name)
    publish_index(resource_id, index_name)


def transform_to_index_entry(resource: resourcemgr.Resource, src_entry: Dict, fields):
    index_entry = indexer.impl.create_empty_object()
    _transform_to_index_entry(resource, src_entry, index_entry, fields)
    return index_entry


def _evaluate_function(function_conf, src_entry, src_resource):
    if 'multi_ref' in function_conf:
        function_conf = function_conf['multi_ref']
        target_field = function_conf['field']
        if 'resource_id' in function_conf:
            target_resource = resourcemgr.get_resource(function_conf['resource_id'], function_conf['resource_version'])
        else:
            target_resource = src_resource

        if 'test' in function_conf:
            operator, args = list(function_conf['test'].items())[0]
            filters = {'deleted': False}
            if operator == 'equals':
                for arg in args:
                    if 'self' in arg:
                        filters[target_field] = src_entry[arg['self']]
                    else:
                        raise NotImplementedError()
                target_entries = entryread.get_entries_by_column(target_resource, filters)
            elif operator == 'contains':
                for arg in args:
                    if 'self' in arg:
                        filters[target_field] = src_entry[arg['self']]
                    else:
                        raise NotImplementedError()
                target_entries = entryread.get_entries_by_column(target_resource, filters)
            else:
                raise NotImplementedError()
        else:
            raise NotImplementedError()

        res = indexer.impl.create_empty_list()
        for entry in target_entries:
            index_entry = indexer.impl.create_empty_object()
            list_of_sub_fields = ("tmp", function_conf['result']),
            _transform_to_index_entry(target_resource, {'tmp': entry['entry']}, index_entry, list_of_sub_fields)
            indexer.impl.add_to_list_field(res, index_entry["tmp"])
    else:
        raise NotImplementedError()
    return res


def _transform_to_index_entry(resource: resourcemgr.Resource, _src_entry: Dict, _index_entry, fields):
    for field_name, field_conf in fields:
        if field_conf.get('virtual', False):
            res = _evaluate_function(field_conf['function'], _src_entry, resource)
            if res:
                indexer.impl.assign_field(_index_entry, field_name, res)
        elif field_conf['type'] == 'object':
            new_object = indexer.impl.create_empty_object()
            if field_name in _src_entry:
                _transform_to_index_entry(resource, _src_entry[field_name],
                                          new_object, field_conf['fields'].items())
            indexer.impl.assign_field(_index_entry, field_name, new_object)
        elif field_conf.get('ref', {}):
            ref_field = field_conf['ref']
            if ref_field.get('resource_id'):
                ref_resource = resourcemgr.get_resource(ref_field['resource_id'], version=ref_field['resource_version'])
                if ref_field['field'].get('collection'):
                    ref_objs = []
                    for ref_id in _src_entry[field_name]:
                        ref_entry_body = entryread.get_entry_by_entry_id(ref_resource, str(ref_id))
                        if ref_entry_body:
                            ref_entry = {field_name: json.loads(ref_entry_body.body)}
                            ref_index_entry = {}
                            list_of_sub_fields = (field_name, ref_field['field']),
                            _transform_to_index_entry(resource, ref_entry, ref_index_entry, list_of_sub_fields)
                            ref_objs.append(ref_index_entry[field_name])
                    indexer.impl.assign_field(_index_entry, field_name, ref_objs)
                else:
                    raise NotImplementedError()
            else:
                # TODO this assumes non-collection, fix
                ref_id = _src_entry.get(field_name)
                if ref_id:
                    ref_entry = {field_name: json.loads(entryread.get_entry_by_entry_id(resource, str(ref_id)).body)}
                    ref_index_entry = {}
                    list_of_sub_fields = (field_name, ref_field['field']),
                    _transform_to_index_entry(resource, ref_entry, ref_index_entry, list_of_sub_fields)
                    indexer.impl.assign_field(_index_entry, field_name, ref_index_entry[field_name])
        else:
            indexer.impl.assign_field(_index_entry, field_name, _src_entry.get(field_name))