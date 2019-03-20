from typing import Optional
import json
import collections

from karp.resourcemgr import get_resource
from .resource import Resource
import karp.util.jsondiff as jsondiff
import karp.errors as errors


def get_entries_by_column(resource_obj: Resource, filters):
    config = resource_obj.config
    cls = resource_obj.model
    query = cls.query

    joined_filters = []
    simple_filters = {}

    for filter_key in filters.keys():
        tmp = collections.defaultdict(dict)
        if filter_key in config['referenceable'] and config['fields'][filter_key].get('collection', False):
            child_cls = cls.child_tables[filter_key]
            tmp[child_cls.__tablename__][filter_key] = filters[filter_key]
        else:
            simple_filters[filter_key] = filters[filter_key]
        joined_filters.extend(tmp.values())

    query = query.filter_by(**simple_filters)

    for child_filters in joined_filters:
        child_cls = cls.child_tables[list(child_filters.keys())[0]]
        query = query.join(child_cls).filter_by(**child_filters)

    return [{'id': db_entry.id, 'entry_id': db_entry.entry_id, 'entry': json.loads(db_entry.body)} for db_entry in query]


def get_entry(resource_id: str, entry_id: str, version: Optional[int]=None):
    resource = get_resource(resource_id, version=version)
    return get_entry_by_entry_id(resource, entry_id)


def get_entry_by_entry_id(resource: Resource, entry_id: str):
    cls = resource.model
    return cls.query.filter_by(entry_id=entry_id).first()


def diff(resource_obj: Resource, entry_id: str, version1: int, version2: int):
    src = resource_obj.model.query.filter_by(entry_id=entry_id).first()
    obj1 = resource_obj.history_model.query.filter_by(entry_id=src.id, version=version1).first()
    obj2 = resource_obj.history_model.query.filter_by(entry_id=src.id, version=version2).first()
    if not obj1:
        raise errors.EntryNotFoundError(resource_obj.config['resource_id'], entry_id, entry_version=version1)
    if not obj2:
        raise errors.EntryNotFoundError(resource_obj.config['resource_id'], entry_id, entry_version=version2)
    return jsondiff.compare(json.loads(obj1.body), json.loads(obj2.body))
