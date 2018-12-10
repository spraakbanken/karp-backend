import json
import fastjsonschema
import logging

from karp.errors import KarpError
from karp.resourcemgr import get_resource
from karp.database import db
from karp.resourcemgr.index import index_mgr

_logger = logging.getLogger(__name__)


def get_entries(resource_id):
    cls = get_resource(resource_id).model
    entries = cls.query.filter_by(deleted=False)
    return [{'id': db_entry.id, 'entry': json.loads(db_entry.body)} for db_entry in entries]


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
        kwargs = {
            'body': entry_json
        }
        id_field = resource_conf.get('id')
        if id_field:
            kwargs[id_field] = entry[id_field]
        db_entry = resource.model(**kwargs)
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
            yield (db_entry.id, _prepare_entry(resource, entry))

    if resource.active:
        index_mgr.add_entries(resource_id, index_entries(created_db_entries))


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


def _prepare_entry(resource, entry):
    """
    Make a "db entry" into an "index entry". Here for future functionality.
    """
    return json.dumps(entry)


def _validate_and_prepare_entry(resource, entry):
    validate_entry = _compile_schema(resource.entry_json_schema)
    _validate_entry(validate_entry, entry)
    entry_json = _prepare_entry(resource, entry)
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
            entry=json.dumps(object, indent=2),
            message=e.message
        ))
