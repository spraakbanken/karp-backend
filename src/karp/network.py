from typing import Dict
import json
import collections

from karp.resourcemgr import get_resource
import karp.resourcemgr.entryread as entryread
from karp.errors import KarpError


def get_referenced_entries(resource_id: str, version: int, entry_id: str):
    refs = []

    def create_ref(resource_id: str, resource_version: int, entry_id: str, entry_body: Dict):
        return {
            'resource_id': resource_id,
            'resource_version': resource_version,
            'id': entry_id,
            'entry': entry_body
        }

    resource_refs, resource_backrefs = get_ref_config(resource_id, version)
    src_entry = entryread.get_entry(resource_id, entry_id, version=version)
    if not src_entry:
        return KarpError('Entry not found')
    src_body = json.loads(src_entry.body)

    for (resource_id, resource_version), fields in resource_backrefs.items():
        resource = get_resource(resource_id, version=version)
        for field_name in fields.keys():
            for entry in entryread.get_entries_by_column(resource, {field_name: entry_id}):
                ref_entry_id = entry['id']
                ref_entry_body = entry['entry']
                yield create_ref(resource_id, resource_version, ref_entry_id, ref_entry_body)

    for (resource_id, resource_version), fields in resource_refs.items():
        for field_name, field in fields.items():
            ids = src_body.get(field_name)
            if field.get('collection', False):
                for ref_entry_id in ids:
                    entry = entryread.get_entry(resource_id, ref_entry_id, version=resource_version)
                    if entry:
                        yield create_ref(resource_id, resource_version, entry.entry_id, json.loads(entry.body))
            else:
                entry = entryread.get_entry(resource_id, ids, version=resource_version)
                if entry:
                    yield create_ref(resource_id, resource_version, entry.entry_id, json.loads(entry.body))


def get_ref_config(resource_id: str, version: int):
    """
    TODO move this to the Resource class?
    Goes through all configs loooking for references to this resource
    """
    src_resource = get_resource(resource_id, version=version)
    resource_backrefs = collections.defaultdict(collections.defaultdict)
    resource_refs = collections.defaultdict(collections.defaultdict)

    # TODO this needs to be replaced with actual resources
    if resource_id == 'places':
        all_other_resources = [get_resource('municipalities', version=1)]
    else:
        all_other_resources = [get_resource('places', version=1)]

    for field_name, field in src_resource.config['fields'].items():
        if 'ref' in field:
            if 'resource_id' not in field['ref']:
                resource_backrefs[(resource_id, version)][field_name] = field
                resource_refs[(resource_id, version)][field_name] = field
            else:
                resource_refs[(field['ref']['resource_id'], field['ref']['resource_version'])][field_name] = field

    for other_resource in all_other_resources:
        for field_name, field in other_resource.config['fields'].items():
            ref = field.get('ref')
            if ref and ref.get('resource_id') == resource_id and ref.get('resource_version') == version:
                resource_backrefs[(other_resource.config['resource_id'], other_resource.version)][field_name] = field
    return resource_refs, resource_backrefs
