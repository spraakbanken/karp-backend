import json

from typing import BinaryIO
from typing import Tuple
from typing import Dict
from typing import List

import fastjsonschema  # pyre-ignore

from flask import current_app  # pyre-ignore
import elasticsearch.helpers  # pyre-ignore

from karp import get_resource_string
from karp.database import ResourceDefinition
from karp.database import get_or_create_resource_model
from karp.database import db
from karp.database import get_latest_resource_definition
from karp.database import get_next_resource_version
from karp.database import get_active_resource_definition
from karp.database import get_resource_definition

from karp.util.json_schema import create_entry_json_schema

from .resource import ResourceConfig


resource_classes = {}
resource_config_cache: Dict = {}


def get_available_resources() -> List[ResourceDefinition]:
    return ResourceDefinition.query.filter_by(active=True)


def get_resource(id: str):
    return resource_classes[id]


def get_resource_config(id: str) -> ResourceConfig:
    resource_config = resource_config_cache[id]
    if not resource_config:
        resource_config = update_resource_config(id)
    return ResourceConfig(resource_config)




def setup_resource_classes():
    for resource in get_available_resources():
        config = json.loads(resource.config_file)
        resource_config_cache[config['resource_id']] = config
        resource_classes[config['resource_id']] = create_sqlalchemy_class(config, resource.version)


def setup_resource_class(resource_id, version=None):
    if version:
        resource = get_resource_definition(resource_id, version)
    else:
        resource = get_active_resource_definition(resource_id)
    config = json.loads(resource.config_file)
    resource_config_cache[resource_id] = config
    resource_classes[config['resource_id']] = create_sqlalchemy_class(config, resource.version)


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

    sqlalchemyclass = create_sqlalchemy_class(config, version)

    sqlalchemyclass.__table__.create(bind=db.engine)

    search.create_index(resource_id, version, config)

    return resource['resource_id'], resource['version']


def publish_resource(resource_id, version):
    resource = get_resource_definition(resource_id, version)
    old_active = get_active_resource_definition(resource_id)
    if old_active:
        old_active.active = False
    resource.active = True
    db.session.commit()

    config = json.loads(resource.config_file)
    resource_config_cache[resource_id] = config
    # this stuff doesn't matter right now since we are not modifying the state of the actual app, only the CLI
    resource_classes[resource_id] = create_sqlalchemy_class(config, resource.version)


def unpublish_resource(resource_id):
    resource = get_active_resource_definition(resource_id)
    if resource:
        resource.active = False
        db.session.update(resource)
        db.session.commit()
    del resource_classes[resource_id]


def delete_resource(resource_id, version):
    resource = get_resource_definition(resource_id, version)
    resource.deleted = True
    resource.active = False
    db.session.update(resource)
    db.session.commit()


def get_entries(resource, version=None):
    cls = resource_classes[resource]
    entries = cls.query.all()
    return entries


def add_entry(resource_id, entry):
    # TODO add to which version?
    resource_def = get_active_resource_definition(resource_id)
    version = resource_def.version
    add_entries(resource_id, version, [entry])


def add_entries(resource_id, version, entries):
    cls = resource_classes[resource_id]

    resource_def = get_resource_definition(resource_id, version)
    try:
        schema = json.loads(resource_def.entry_json_schema)
        validate_entry = fastjsonschema.compile(schema)
    except fastjsonschema.JsonSchemaDefinitionException as e:
        raise RuntimeError(e)

    created_db_entries = []
    for entry in entries:
        try:
            validate_entry(entry)
        except fastjsonschema.JsonSchemaException as e:
            raise RuntimeError(e)

        entry_json = json.dumps(entry)
        kwargs = {
            'body': entry_json
        }
        id_field = json.loads(resource_def.config_file).get('id')
        if id_field:
            kwargs[id_field] = entry[id_field]
        db_entry = cls(**kwargs)
        created_db_entries.append((db_entry, entry))
        db.session.add(db_entry)

    db.session.commit()

    search.add_entries(resource_id, version, created_db_entries)


def delete_entry(resource, entry_id, version=None):
    cls = resource_classes[resource]
    entry = cls.query.filter_by(id=entry_id).first()
    db.session.delete(entry)
    db.session.commit()


def get_entry(resource, entry_id, version=None):
    cls = resource_classes[resource]
    entry = cls.query.filter_by(id=entry_id).first()
    return entry
