import json
import logging

from karp.resourcemgr import get_resource
from karp.search import search
from .resource import Resource

_logger = logging.getLogger(__name__)


def get_entries(resource_id):
    cls = get_resource(resource_id).model
    entries = cls.query.filter_by(deleted=False)
    return [{'id': db_entry.id, 'entry': json.loads(db_entry.body)} for db_entry in entries]


def get_entries_by_column(resource_obj: Resource, filters):
    config = resource_obj.config
    cls = resource_obj.model
    query = cls.query
    delete = []
    for filter_key in filters.keys():
        if filter_key in config['referenceable'] and config['fields'][filter_key].get('collection', False):
            child_cls = cls.child_tables[filter_key]
            query = query.join(child_cls).filter_by(**{filter_key: filters[filter_key]})
            delete.append(filter_key)
    for del_key in delete:
        del filters[del_key]

    entries = query.filter_by(**filters)
    return [{'id': db_entry.id, 'entry': json.loads(db_entry.body)} for db_entry in entries]


def get_entries_indexed(resource_id):
    res = search.search((resource_id,))
    return res


def get_entry(resource, entry_id, version=None):
    cls = get_resource(resource, version=version).model
    entry = cls.query.filter_by(id=entry_id).first()
    return entry


def get_entry_by_entry_id(resource: Resource, entry_id: str):
    cls = resource.model
    entry = cls.query.filter_by(entry_id=entry_id).first()
    return entry
