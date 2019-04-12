from typing import Optional, Dict
import json
import collections
from datetime import datetime

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


def diff(resource_obj: Resource, entry_id: str, from_version: int=None, to_version: int=None, from_date: datetime=None,
         to_date: datetime=None, entry: Optional[Dict]=None):
    src = resource_obj.model.query.filter_by(entry_id=entry_id).first()

    query = resource_obj.history_model.query.filter_by(entry_id=src.id)
    timestamp_field = resource_obj.history_model.timestamp

    if from_version:
        obj1_query = query.filter_by(version=from_version)
    elif from_date:
        obj1_query = query.filter(timestamp_field >= from_date).order_by(timestamp_field)
    else:
        obj1_query = query.order_by(timestamp_field)
    if to_version:
        obj2_query = query.filter_by(version=to_version)
    elif to_date:
        obj2_query = query.filter(timestamp_field <= to_date).order_by(timestamp_field.desc())
    else:
        obj2_query = None

    obj1 = obj1_query.first()
    obj1_body = json.loads(obj1.body) if obj1 else None

    if obj2_query:
        obj2 = obj2_query.first()
        obj2_body = json.loads(obj2.body) if obj2 else None
    elif entry:
        obj2_body = entry
    else:
        obj2 = query.order_by(timestamp_field.desc()).first()
        obj2_body = json.loads(obj2.body) if obj2 else None

    if not obj1_body or not obj2_body:
        raise errors.KarpError('diff impossible!')

    return jsondiff.compare(obj1_body, obj2_body)
