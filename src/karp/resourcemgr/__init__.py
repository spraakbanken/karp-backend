import json
from typing import BinaryIO
from typing import Tuple
from typing import Dict
from typing import List
import fastjsonschema  # pyre-ignore
import logging
import collections
from sqlalchemy.sql import func

from karp import get_resource_string
from karp.database import ResourceDefinition
from karp.database import db
from karp import database
from karp.util.json_schema import create_entry_json_schema
from karp.errors import ResourceNotFoundError
from .resource import Resource

_logger = logging.getLogger('karp')

resource_models = {}  # Dict
history_models = {}  # Dict
resource_configs = {}  # Dict
resource_versions = {}  # Dict[str, int]


def get_available_resources() -> List[ResourceDefinition]:
    return ResourceDefinition.query.filter_by(active=True)


def get_resource(resource_id: str, version: int = None) -> Resource:
    if not version:
        resource_def = database.get_active_resource_definition(resource_id)
        if not resource_def:
            raise ResourceNotFoundError(resource_id)
        if resource_id not in resource_models:
            setup_resource_class(resource_id)
        return Resource(model=resource_models[resource_id],
                        history_model=history_models[resource_id],
                        resource_def=resource_def,
                        version=resource_versions[resource_id],
                        config=resource_configs[resource_id])
    else:
        resource_def = database.get_resource_definition(resource_id, version)
        if not resource_def:
            raise ResourceNotFoundError(resource_id, version=version)
        config = json.loads(resource_def.config_file)
        cls = database.get_or_create_resource_model(config, version)
        history_cls = database.get_or_create_history_model(resource_id, version)
        return Resource(model=cls,
                        history_model=history_cls,
                        resource_def=resource_def,
                        version=version,
                        config=config)


def get_all_resources()-> List[ResourceDefinition]:
    return ResourceDefinition.query.all()


def create_and_update_caches(id: str,
                             version: int,
                             config: Dict) -> None:
    resource_models[id] = database.get_or_create_resource_model(config, version)
    history_models[id] = database.get_or_create_history_model(id, version)
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
        resource_def = database.get_resource_definition(resource_id, version)
    else:
        resource_def = database.get_active_resource_definition(resource_id)
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

    version = database.get_next_resource_version(resource_id)

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

    sqlalchemyclass = database.get_or_create_resource_model(config, version)
    history_model = database.get_or_create_history_model(resource_id, version)
    sqlalchemyclass.__table__.create(bind=db.engine)
    for child_class in sqlalchemyclass.child_tables.values():
        child_class.__table__.create(bind=db.engine)
    history_model.__table__.create(bind=db.engine)

    return resource['resource_id'], resource['version']


def publish_resource(resource_id, version):
    resource = database.get_resource_definition(resource_id, version)
    old_active = database.get_active_resource_definition(resource_id)
    if old_active:
        old_active.active = False
    resource.active = True
    db.session.commit()

    config = json.loads(resource.config_file)
    # this stuff doesn't matter right now since we are not modifying the state of the actual app, only the CLI
    create_and_update_caches(resource_id, resource.version, config)


def unpublish_resource(resource_id):
    resource = database.get_active_resource_definition(resource_id)
    if resource:
        resource.active = False
        db.session.update(resource)
        db.session.commit()
    remove_from_caches(resource_id)


def delete_resource(resource_id, version):
    resource = database.get_resource_definition(resource_id, version)
    resource.deleted = True
    resource.active = False
    db.session.update(resource)
    db.session.commit()


def get_refs(resource_id, version=None):
    """
    Goes through all other resource configs finding resources and fields that refer to this resource
    """
    resource_backrefs = collections.defaultdict(lambda: collections.defaultdict(dict))
    resource_refs = collections.defaultdict(lambda: collections.defaultdict(dict))

    src_resource = get_resource(resource_id, version=version)

    all_other_resources = [resource_def for resource_def in get_all_resources()
                           if resource_def.resource_id != resource_id or resource_def.version != version]

    for field_name, field in src_resource.config['fields'].items():
        if 'ref' in field:
            if 'resource_id' not in field['ref']:
                resource_backrefs[resource_id][version][field_name] = field
                resource_refs[resource_id][version][field_name] = field
            else:
                resource_refs[field['ref']['resource_id']][field['ref']['resource_version']][field_name] = field
        elif 'function' in field and 'multi_ref' in field['function']:
            virtual_field = field['function']['multi_ref']
            ref_field = virtual_field['field']
            if 'resource_id' in virtual_field:
                resource_backrefs[virtual_field['resource_id']][virtual_field['resource_version']][ref_field] = None
            else:
                resource_backrefs[resource_id][version][ref_field] = None

    for resource_def in all_other_resources:
        other_resource = get_resource(resource_def.resource_id, version=resource_def.version)
        for field_name, field in other_resource.config['fields'].items():
            ref = field.get('ref')
            if ref and ref.get('resource_id') == resource_id and ref.get('resource_version') == version:
                resource_backrefs[resource_def.resource_id][resource_def.version][field_name] = field


    def flatten_dict(ref_dict):
        ref_list = []
        for ref_resource_id, versions in ref_dict.items():
            for ref_version, field_names in versions.items():
                for field_name, field in field_names.items():
                    ref_list.append((ref_resource_id, ref_version, field_name, field))
        return ref_list

    return flatten_dict(resource_refs), flatten_dict(resource_backrefs)


def is_protected(resource_id, level):
    """
    Level can be READ, WRITE or ADMIN
    """
    resource = get_resource(resource_id)
    protection = resource.config.get('protected', {})
    return protection.get('read') or \
           protection.get('write') and level != 'READ' or \
           protection.get('admin') and level == 'ADMIN'


def get_all_versions(resource_obj: Resource) -> Dict[int, int]:
    history_table = resource_obj.history_model
    result = db.session.query(
        history_table.entry_id, func.max(history_table.version)
    ).group_by(history_table.entry_id)
    return {row[0]: row[1] for row in result}


def get_version(resource_def: Resource, _id: int) -> int:
    history_table = resource_def.history_model
    result = db.session.query(
        func.max(history_table.version)
    ).filter(history_table.entry_id == _id).group_by(history_table.entry_id)
    return [row[0] for row in result][0]
