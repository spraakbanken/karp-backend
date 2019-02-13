import json
import fastjsonschema  # pyre-ignore
import logging

from karp.errors import KarpError
from karp.resourcemgr import get_resource
from karp.database import db
import karp.indexmgr as indexmgr
from .resource import Resource
from typing import Dict, List

_logger = logging.getLogger('karp')


def add_entry(resource_id: str, entry: Dict, user_id: str, message: str=None, resource_version: int=None):
    add_entries(resource_id, [entry], user_id, message=message, resource_version=resource_version)


def preview_entry(resource_id, entry, resource_version=None):
    resource = get_resource(resource_id, version=resource_version)
    entry_json = _validate_and_prepare_entry(resource, entry)
    return entry_json


def update_entry(resource_id: str, entry_id: str, version: int, entry: Dict, user_id: str,
                 message: str=None, resource_version: int=None):
    resource = get_resource(resource_id, version=resource_version)

    index_entry_json = _validate_and_prepare_entry(resource, entry)

    current_db_entry = resource.model.query.filter_by(entry_id=entry_id, deleted=False).first()
    if not current_db_entry:
        raise KarpError('No entry in resource {resource_id} with id {entry_id}'.format(
            resource_id=resource_id,
            entry_id=entry_id
        ))

    db_entry_json = json.dumps(entry)
    db_id = current_db_entry.id
    latest_history_entry = resource.history_model.query.filter_by(entry_id=db_id).order_by(
        resource.history_model.version.desc()).first()
    if latest_history_entry.version > version:
        raise KarpError('Version conflict. Please update entry.')
    history_entry = resource.history_model(
        entry_id=db_id,
        user_id=user_id,
        body=db_entry_json,
        version=latest_history_entry.version + 1,
        op='UPDATE',
        message=message
    )

    kwargs = _src_entry_to_db_kwargs(entry, db_entry_json, resource.model, resource.config)
    for key, value in kwargs.items():
        setattr(current_db_entry, key, value)

    db.session.add(history_entry)
    db.session.commit()

    indexmgr.add_entries(resource_id, [(entry_id, latest_history_entry.version + 1, index_entry_json)])


def add_entries_from_file(resource_id: str, version: int, data: str) -> int:
    with open(data) as fp:
        objs = []
        for line in fp:
            objs.append(json.loads(line))
        add_entries(resource_id, objs, user_id='local_admin', resource_version=version)
    return len(objs)


def add_entries(resource_id: str, entries: List[Dict], user_id: str, message: str=None, resource_version: int=None):
    resource = get_resource(resource_id, version=resource_version)
    resource_conf = resource.config

    validate_entry = _compile_schema(resource.entry_json_schema)

    created_db_entries = []
    for entry in entries:
        _validate_entry(validate_entry, entry)

        entry_json = json.dumps(entry)
        db_entry = _src_entry_to_db_entry(entry, entry_json, resource.model, resource_conf)
        created_db_entries.append((db_entry, entry, entry_json))
        db.session.add(db_entry)

    db.session.commit()

    for db_entry, entry, entry_json in created_db_entries:
        history_entry = resource.history_model(
            entry_id=db_entry.id,
            user_id=user_id,
            body=entry_json,
            version=1,
            op='ADD',
            message=message
        )
        db.session.add(history_entry)
    db.session.commit()

    if resource.active:
        indexmgr.add_entries(resource_id,
                             [(db_entry.entry_id, 1, _src_entry_to_index_entry(resource, entry))
                              for db_entry, entry, _ in created_db_entries])


def _src_entry_to_db_entry(entry, entry_json, resource_model, resource_conf):
    kwargs = _src_entry_to_db_kwargs(entry, entry_json, resource_model, resource_conf)
    db_entry = resource_model(**kwargs)
    return db_entry


def _src_entry_to_db_kwargs(entry, entry_json, resource_model, resource_conf):
    kwargs = {
        'body': entry_json
    }

    for field_name in resource_conf.get('referenceable', ()):
        field_val = entry.get(field_name)
        if resource_conf['fields'][field_name].get('collection', False):
            child_table = resource_model.child_tables[field_name]
            for elem in field_val:
                if field_name not in kwargs:
                    kwargs[field_name] = []
                kwargs[field_name].append(child_table(**{field_name: elem}))
        else:
            if field_val:
                kwargs[field_name] = field_val
    id_field = resource_conf.get('id')
    if id_field:
        kwargs['entry_id'] = entry[id_field]
    else:
        kwargs['entry_id'] = 'TODO'  # generate id for resources that are missing it
    return kwargs


def delete_entry(resource_id: str, entry_id: str, user_id: str):
    resource = get_resource(resource_id)
    entry = resource.model.query.filter_by(entry_id=entry_id, deleted=False).first()
    if not entry:
        raise RuntimeError('no entry with id {entry_id} found'.format(entry_id=entry_id))
    entry.deleted = True
    history_cls = resource.history_model
    history_entry = history_cls(
        entry_id=entry.id,
        user_id=user_id,
        op='DELETE',
        version=-1
    )
    db.session.add(history_entry)
    db.session.commit()
    indexmgr.delete_entry(resource_id, entry.entry_id)


def _src_entry_to_index_entry(resource: Resource, src_entry: Dict):
    """
    Make a "src entry" into an "index entry"
    """
    return indexmgr.transform_to_index_entry(resource, src_entry, resource.config['fields'].items())


def _validate_and_prepare_entry(resource, entry):
    validate_entry = _compile_schema(resource.entry_json_schema)
    _validate_entry(validate_entry, entry)
    return _src_entry_to_index_entry(resource, entry)


def _compile_schema(json_schema):
    try:
        validate_entry = fastjsonschema.compile(json_schema)
        return validate_entry
    except fastjsonschema.JsonSchemaDefinitionException as e:
        raise RuntimeError(e)


def _validate_entry(schema, json_obj):
    try:
        schema(json_obj)
    except fastjsonschema.JsonSchemaException as e:
        _logger.warning('Entry not valid:\n{entry}\nMessage: {message}'.format(
            entry=json.dumps(json_obj, indent=2),
            message=e.message
        ))
        raise ValueError()
