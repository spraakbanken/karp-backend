import json

from typing import BinaryIO
from typing import Tuple

import fastjsonschema  # pyre-ignore

from karp import get_resource_string
from karp.database import Resources
from karp.database import create_sqlalchemy_class
from karp.database import db

from karp.util.json_schema import create_entry_json_schema

from .resource import Resource  # noqa: F401


resource_classes = {}


def get_available_resources():
    return Resources.query.filter_by(active=True)


def get_resource(id: str) -> Resource:
    return Resource(resource_classes[id])


def setup_resource_classes():
    for resource in get_available_resources():
        config = json.loads(resource.config_file)
        resource_classes[config['resource_id']] = create_sqlalchemy_class(config, resource.version)


def setup_resource_class(resource_id, version=None):
    if version:
        resource = Resources.query.filter_by(resource_id=resource_id, version=version).first()
    else:
        resource = Resources.query.filter_by(resource_id=resource_id, active=True).first()
    config = json.loads(resource.config_file)
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

    latest_resource = (
        Resources.query
                .filter_by(resource_id=resource_id)
                .order_by(Resources.version.desc())
                .first()
    )
    if latest_resource:
        version = latest_resource.version + 1
    else:
        version = 1

    entry_json_schema = create_entry_json_schema(config)

    resource = {
        'resource_id': resource_id,
        'version': version,
        'config_file': json.dumps(config),
        'entry_json_schema': json.dumps(entry_json_schema)
    }

    new_resource = Resources(**resource)
    db.session.add(new_resource)
    db.session.commit()

    sqlalchemyclass = create_sqlalchemy_class(config, version)

    sqlalchemyclass.__table__.create(bind=db.engine)

    search.create_index(resource_id, version, config)

    return resource['resource_id'], resource['version']


def publish_resource(resource_id, version):
    resource = Resources.query.filter_by(resource_id=resource_id, version=version).first()
    old_active = Resources.query.filter_by(resource_id=resource_id, version=version, active=True).first()
    if old_active:
        old_active.active = False
    resource.active = True
    db.session.commit()

    config = json.loads(resource.config_file)

    # this stuff doesn't matter right now since we are not modifying the state of the actual app, only the CLI
    resource_classes[config['resource_id']] = create_sqlalchemy_class(config, resource.version)


def unpublish_resource(resource_id):
    resource = Resources.query.filter_by(resource_id=resource_id, active=True).first()
    if resource:
        resource.active = False
        db.session.update(resource)
        db.session.commit()
    del resource_classes[resource_id]


def delete_resource(resource_id, version):
    resource = Resources.query.filter_by(resource_id=resource_id, version=version).first()
    resource.deleted = True
    resource.active = False
    db.session.update(resource)
    db.session.commit()


def get_entries(resource, version=None):
    cls = resource_classes[resource]
    entries = cls.query.all()
    return entries


def add_entry(resource_id, entry):
    # TOO add to which version?
    resource_def = Resources.query.filter_by(resource_id=resource_id, active=True).first()
    version = resource_def.version
    add_entries(resource_id, version, [entry])


def add_entries(resource_id, version, entries):
    cls = resource_classes[resource_id]

    resource_def = Resources.query.filter_by(resource_id=resource_id, version=version).first()
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
