import json
import fastjsonschema
import logging

from karp.errors import KarpError
from karp.resourcemgr import get_resource
from karp.database import db
from karp.resourcemgr.index import index_mgr
from karp.search import search
from .resource import Resource
from typing import Dict

_logger = logging.getLogger(__name__)


def get_entries(resource_id):
    cls = get_resource(resource_id).model
    entries = cls.query.filter_by(deleted=False)
    return [{'id': db_entry.id, 'entry': json.loads(db_entry.body)} for db_entry in entries]


def get_entries_by_column(resource_id, filters):
    cls = get_resource(resource_id).model
    entries = cls.query.filter_by(**filters)
    return [{'id': db_entry.id, 'entry': json.loads(db_entry.body)} for db_entry in entries]


def get_entries_indexed(resource_id):
    res = search.search((resource_id,))
    return res


def add_entry(resource_id, entry, message=None, resource_version=None):
    add_entries(resource_id, [entry], message=message, resource_version=resource_version)


def preview_entry(resource_id, entry, resource_version=None):
    resource = get_resource(resource_id, version=resource_version)
    entry_json = _validate_and_prepare_entry(resource, entry)
    return entry_json


def update_entry(resource_id, entry_id, entry, message=None, resource_version=None):
    resource = get_resource(resource_id, version=resource_version)

    entry_json = _validate_and_prepare_entry(resource, entry)

    current_db_entry = resource.model.query.filter_by(id=entry_id, deleted=False).first()
    if not current_db_entry:
        raise KarpError('No entry in resource {resource_id} with id {entry_id}'.format(
            resource_id=resource_id,
            entry_id=entry_id
        ))

    current_db_entry.body = entry_json

    latest_history_entry = resource.history_model.query.filter_by(entry_id=entry_id).\
        order_by(resource.history_model.version.desc()).first()
    history_entry = resource.history_model(
        entry_id=entry_id,
        user_id='TODO',
        body=entry_json,
        version=latest_history_entry.version + 1,
        op='UPDATE',
        message=message
    )
    db.session.add(history_entry)
    db.session.commit()

    index_mgr.add_entries(resource_id, [(entry_id, entry)])


def add_entries(resource_id, entries, message=None, resource_version=None):
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
            user_id='TODO',
            body=entry_json,
            version=1,
            op='ADD',
            message=message
        )
        db.session.add(history_entry)
    db.session.commit()

    def index_entries(entry_db_map):
        for db_entry, entry, _ in entry_db_map:
            yield (db_entry.id, _src_entry_to_index_entry(resource, entry))

    if resource.active:
        index_mgr.add_entries(resource_id, index_entries(created_db_entries))


def _src_entry_to_db_entry(entry, entry_json, resource_model, resource_conf):
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
    db_entry = resource_model(**kwargs)
    return db_entry


def delete_entry(resource_id, entry_id):
    resource = get_resource(resource_id)
    entry = resource.model.query.filter_by(id=entry_id, deleted=False).first()
    if not entry:
        raise RuntimeError('no entry with id {entry_id} found'.format(entry_id=entry_id))
    entry.deleted = True
    history_cls = resource.history_model
    history_entry = history_cls(
        entry_id=entry.id,
        user_id='TODO',
        op='DELETE',
        version=-1
    )
    db.session.add(history_entry)
    db.session.commit()
    index_mgr.delete_entry(resource_id, entry_id)


def get_entry(resource, entry_id, version=None):
    cls = get_resource(resource, version=version).model
    entry = cls.query.filter_by(id=entry_id).first()
    return entry


def get_entry_by_entry_id(resource: Resource, entry_id: str):
    cls = resource.model
    entry = cls.query.filter_by(entry_id=entry_id).first()
    return entry


def _evaluate_function(function_conf, src_entry, src_resource):
    if 'multi_ref' in function_conf:
        function_conf = function_conf['multi_ref']
        target_field = function_conf['field']
        if 'resource_id' in function_conf:
            target_resource = get_resource(function_conf['resource_id'])
        else:
            target_resource = src_resource

        if 'test' in function_conf:
            operator, args = list(function_conf['test'].items())[0]
            filters = {}
            if operator == 'equals':
                for arg in args:
                    if 'self' in arg:
                        filters[target_field] = src_entry[arg['self']]
                    else:
                        raise NotImplementedError()
                target_entries = get_entries_by_column(target_resource.config['resource_id'], filters)
            elif operator == 'contains':
                # TODO implement contains
                raise NotImplementedError()
            else:
                raise NotImplementedError()
        else:
            raise NotImplementedError()

        res = []
        for entry in target_entries:
            index_entry = {}
            list_of_sub_fields = ("tmp", function_conf['result']),
            recursive_something(target_resource, {'tmp': entry['entry']}, index_entry, list_of_sub_fields)
            res.append(index_entry["tmp"])
    else:
        raise NotImplementedError()
    return res


def recursive_something(resource: Resource, _src_entry: Dict, _index_entry: Dict, fields):
    for field_name, field_conf in fields:
        if field_conf.get('virtual', False):
            res = _evaluate_function(field_conf['function'], _src_entry, resource)
            if res:
                _index_entry[field_name] = res
        elif field_conf['type'] == 'object':
            _index_entry[field_name] = {}
            if field_name in _src_entry:
                recursive_something(resource, _src_entry[field_name], _index_entry[field_name], field_conf['fields'].items())
        elif field_conf.get('ref', {}):
            ref_field = field_conf['ref']
            if ref_field.get('resource_id'):
                # TODO this assumes collection, fix
                ref_ids = _src_entry.get(field_name)
                target_resource = get_resource(ref_field['resource_id'])
                all_elems = []
                for ref_id in ref_ids:
                    ref_entry = {field_name: json.loads(get_entry_by_entry_id(target_resource, str(ref_id)).body)}
                    ref_index_entry = {}
                    list_of_sub_fields = (field_name, ref_field['field']),
                    recursive_something(target_resource, ref_entry, ref_index_entry, list_of_sub_fields)
                    all_elems.append(ref_index_entry[field_name])
                    _index_entry[field_name] = ref_index_entry[field_name]
            else:
                # TODO this assumes non-collection, fix
                ref_id = _src_entry.get(field_name)
                if ref_id:
                    ref_entry = {field_name: json.loads(get_entry_by_entry_id(resource, str(ref_id)).body)}
                    ref_index_entry = {}
                    list_of_sub_fields = (field_name, ref_field['field']),
                    recursive_something(resource, ref_entry, ref_index_entry, list_of_sub_fields)
                    _index_entry[field_name] = ref_index_entry[field_name]
        else:
            _index_entry[field_name] = _src_entry.get(field_name)


def _src_entry_to_index_entry(resource: Resource, src_entry: Dict):
    """
    Make a "src entry" into an "index entry"
    """
    index_entry = {}
    recursive_something(resource, src_entry, index_entry, resource.config['fields'].items())
    return json.dumps(index_entry)


def _validate_and_prepare_entry(resource, entry):
    validate_entry = _compile_schema(resource.entry_json_schema)
    _validate_entry(validate_entry, entry)
    entry_json = _src_entry_to_index_entry(resource, entry)
    return entry_json


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
