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


def get_resource(resource_id: str, version: int=None) -> Resource:
    if not version:
        resource_def = get_active_resource_definition(resource_id)
        if not resource_def:
            raise ResourceNotFoundError(resource_id)
        return Resource(model=resource_models[resource_id],
                        history_model=history_models[resource_id],
                        resource_def=resource_def,
                        version=resource_versions[resource_id],
                        config=resource_configs[resource_id])
    else:
        resource_def = get_resource_definition(resource_id, version)
        if not resource_def:
            raise ResourceNotFoundError(resource_id, version=version)
        config = json.loads(resource_def.config_file)
        cls = get_or_create_resource_model(config, version)
        history_cls = get_or_create_history_model(resource_id, version)
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
    for child_class in sqlalchemyclass.child_tables.values():
        child_class.__table__.create(bind=db.engine)
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


def create_index(resource_id, version=None):
    if version:
        resource_def = get_resource_definition(resource_id, version)
    else:
        resource_def = get_active_resource_definition(resource_id)
    config = json.loads(resource_def.config_file)
    return index_mgr.create_index(resource_id, config)


def reindex(resource_id, index_name, version=None):
    resource_obj = get_resource(resource_id, version)
    entries = resource_obj.model.query.all()
    import karp.resourcemgr.entrymgr as entrymgr
    index_mgr.add_entries(index_name,
                          [(entry.id, entrymgr._src_entry_to_index_entry(resource_obj, json.loads(entry.body)))
                           for entry in entries])


def publish_index(resource_id, index_name):
    index_mgr.publish_index(resource_id, index_name)
