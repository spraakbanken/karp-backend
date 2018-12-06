import json

from typing import BinaryIO
from typing import Tuple
from typing import Dict
from typing import List

import fastjsonschema  # pyre-ignore
import logging

from karp import get_resource_string
from karp.database import ResourceDefinition
from karp.database import get_or_create_resource_model, get_or_create_history_model
from karp.database import db
from karp.database import get_next_resource_version
from karp.database import get_active_resource_definition
from karp.database import get_resource_definition

from karp.util.json_schema import create_entry_json_schema
from karp.resourcemgr.index import index_mgr
from karp.errors import ResourceNotFoundError

from .resource import Resource

_logger = logging.getLogger(__name__)

resource_models = {}  # Dict
history_models = {}  # Dict
resource_configs = {}  # Dict
resource_versions = {}  # Dict[str, int]


def get_available_resources() -> List[ResourceDefinition]:
    return ResourceDefinition.query.filter_by(active=True)


def get_resource(id: str) -> Resource:
    return Resource(model=resource_models[id],
                    config=resource_configs[id],
                    version=resource_versions[id])


def get_all_resources()-> List[ResourceDefinition]:
    return ResourceDefinition.query.all()


def create_and_update_caches(id: str,
                             version: int,
                             config: Dict) -> None:
    resource_models[id] = get_or_create_resource_model(config, version)
    history_models[id] = get_or_create_history_model(id, version)
    resource_versions[id] = version
    resource_configs[id] = config


def remove_from_caches(id: str) -> None:
    del resource_models[id]
    del history_models[id]
    del resource_versions[id]
    del resource_configs[id]


def setup_resource_classes() -> None:
    for resource in get_available_resources():
        config = json.loads(resource.config_file)
        create_and_update_caches(config['resource_id'], resource.version, config)


def setup_resource_class(resource_id, version=None):
    if version:
        resource_def = get_resource_definition(resource_id, version)
    else:
        resource_def = get_active_resource_definition(resource_id)
    if not resource_def:
        raise ResourceNotFoundError(resource_id, version)
    config = json.loads(resource_def.config_file)
    create_and_update_caches(resource_id, resource_def.version, config)


def create_new_resource(config_file: BinaryIO) -> Tuple[str, int]:
    config = json.load(config_file)
    try:
        schema = get_resource_string('schema/resourceconf.schema.json')
        validate_conf = fastjsonschema.compile(json.loads(schema))
        validate_conf(config)
    except fastjsonschema.JsonSchemaException as e:
        raise RuntimeError(e)

    resource_id = config['resource_id']

    version = get_next_resource_version(resource_id)

    entry_json_schema = create_entry_json_schema(config)

    resource = {
        'resource_id': resource_id,
        'version': version,
        'config_file': json.dumps(config),
        'entry_json_schema': json.dumps(entry_json_schema)
    }

    new_resource = ResourceDefinition(**resource)
    db.session.add(new_resource)
    db.session.commit()

    sqlalchemyclass = get_or_create_resource_model(config, version)
    history_model = get_or_create_history_model(resource_id, version)
    sqlalchemyclass.__table__.create(bind=db.engine)
    history_model.__table__.create(bind=db.engine)

    return resource['resource_id'], resource['version']


def publish_resource(resource_id, version):
    resource = get_resource_definition(resource_id, version)
    old_active = get_active_resource_definition(resource_id)
    if old_active:
        old_active.active = False
    resource.active = True
    db.session.commit()

    config = json.loads(resource.config_file)
    # this stuff doesn't matter right now since we are not modifying the state of the actual app, only the CLI
    create_and_update_caches(resource_id, resource.version, config)


def unpublish_resource(resource_id):
    resource = get_active_resource_definition(resource_id)
    if resource:
        resource.active = False
        db.session.update(resource)
        db.session.commit()
    remove_from_caches(resource_id)


def delete_resource(resource_id, version):
    resource = get_resource_definition(resource_id, version)
    resource.deleted = True
    resource.active = False
    db.session.update(resource)
    db.session.commit()


def get_entries(resource_id):
    cls = resource_models[resource_id]
    entries = cls.query.all()
    return [json.loads(db_entry.body) for db_entry in entries]


def add_entry(resource_id, entry, message=None, resource_version=None):
    add_entries(resource_id, [entry], message=message, resource_version=resource_version)


def _entry_json_move_this(json_schema):
    try:
        schema = json.loads(json_schema)
        validate_entry = fastjsonschema.compile(schema)
        return validate_entry
    except fastjsonschema.JsonSchemaDefinitionException as e:
        raise RuntimeError(e)


def _entry_validate_move_this(schema, json_obj):
    try:
        schema(json_obj)
    except fastjsonschema.JsonSchemaException as e:
        _logger.warning('Entry not valid:\n{entry}\nMessage: {message}'.format(
            entry=json.dumps(object, indent=2),
            message=e.message
        ))


def add_entries(resource_id, entries, message=None, resource_version=None):
    if not resource_version:
        resource_def = get_active_resource_definition(resource_id)
        cls = resource_models[resource_id]
        history_cls = history_models[resource_id]
    else:
        resource_def = get_resource_definition(resource_id, resource_version)
        cls = get_or_create_resource_model(json.loads(resource_def.config_file), resource_version)
        history_cls = get_or_create_history_model(resource_id, resource_version)
    resource_conf = json.loads(resource_def.config_file)

    validate_entry = _entry_json_move_this(resource_def.entry_json_schema)

    created_db_entries = []
    for entry in entries:
        _entry_validate_move_this(validate_entry, entry)

        entry_json = json.dumps(entry)
        kwargs = {
            'body': entry_json
        }
        id_field = resource_conf.get('id')
        if id_field:
            kwargs[id_field] = entry[id_field]
        db_entry = cls(**kwargs)
        created_db_entries.append((db_entry, entry, entry_json))
        db.session.add(db_entry)

    db.session.commit()

    for db_entry, entry, entry_json in created_db_entries:
        history_entry = history_cls(
            entry_id=db_entry.id,
            user_id='TODO',
            body=entry_json,
            version=-1,
            op='ADD'
        )
        db.session.add(history_entry)
    db.session.commit()

    def index_entries(entry_db_map):
        for db_entry, entry, _ in entry_db_map:
            yield (db_entry.id, entry)

    if resource_def.active:
        index_mgr.add_entries(resource_id, index_entries(created_db_entries))


def delete_entry(resource_id, entry_id):
    resource_cls = resource_models[resource_id]
    entry = resource_cls.query.filter_by(id=entry_id, deleted=False).first()
    if not entry:
        raise RuntimeError('no entry with id {entry_id} found'.format(entry_id=entry_id))
    entry.deleted = True
    history_cls = history_models[resource_id]
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
    cls = resource_models[resource]
    entry = cls.query.filter_by(id=entry_id).first()
    return entry


def create_index(resource_id, version=None):
    if version:
        resource_def = get_resource_definition(resource_id, version)
    else:
        resource_def = get_active_resource_definition(resource_id)
    config = json.loads(resource_def.config_file)
    return index_mgr.create_index(resource_id, config)


def reindex(resource_id, index_name, version=None):
    setup_resource_class(resource_id, version=version)
    entries = resource_models[resource_id].query.all()
    index_mgr.add_entries(index_name, [(entry, json.loads(entry.body)) for entry in entries])


def publish_index(resource_id, index_name):
    index_mgr.publish_index(resource_id, index_name)
