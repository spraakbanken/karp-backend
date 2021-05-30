from typing import IO, Tuple, Dict, List, Optional
import json
import logging
from pathlib import Path
import collections
import os
import re

from sqlalchemy.sql import func

import fastjsonschema  # pyre-ignore

from sb_json_tools import jsondiff

from karp.domain import commands, model
from . import context
from karp.domain.models.resource import Resource
# from karp.domain.services import indexing

from karp import errors

from karp.application import ctx

# from karp.infrastructure.unit_of_work import unit_of_work

# from karp import get_resource_string
# from karp.database import db
# from karp import database
# from karp.util.json_schema import create_entry_json_schema
# from karp.errors import KarpError
# from karp.errors import ClientErrorCodes
# from karp.errors import (
#     ResourceNotFoundError,
#     ResourceInvalidConfigError,
#     ResourceConfigUpdateError,
# )
# from karp.errors import PluginNotFoundError
# from .resource import Resource
# from karp.resourcemgr.entrymetadata import EntryMetadata

_logger = logging.getLogger("karp")

resource_models = {}  # Dict
history_models = {}  # Dict
resource_configs = {}  # Dict
resource_versions = {}  # Dict[str, int]
field_translations = {}  # Dict[str, Dict[str, List[str]]]


def get_published_resources() -> List[Resource]:
    with unit_of_work(using=ctx.resource_repo) as uw:
        return uw.get_published_resources()


def get_field_translations(resource_id: str) -> Optional[Dict]:
    with unit_of_work(using=ctx.resource_repo) as uw:
        resource = uw.by_resource_id(resource_id)
        return resource.config.get("field_mapping") if resource else None


# def get_resource(resource_id: str, version: Optional[int] = None) -> Resource:
#     if not version:
#         resource_def = database.get_active_resource_definition(resource_id)
#         if not resource_def:
#             raise ResourceNotFoundError(resource_id)
#         if resource_id not in resource_models:
#             setup_resource_class(resource_id)
#         return Resource(
#             model=resource_models[resource_id],
#             history_model=history_models[resource_id],
#             resource_def=resource_def,
#             version=resource_versions[resource_id],
#             config=resource_configs[resource_id],
#         )
#     else:
#         resource_def = database.get_resource_definition(resource_id, version)
#         if not resource_def:
#             raise ResourceNotFoundError(resource_id, version=version)
#         config = json.loads(resource_def.config_file)
#         cls = database.get_or_create_resource_model(config, version)
#         history_cls = database.get_or_create_history_model(resource_id, version)
#         return Resource(
#             model=cls,
#             history_model=history_cls,
#             resource_def=resource_def,
#             version=version,
#             config=config,
#         )


# def get_all_resources() -> List[database.ResourceDefinition]:
#     return database.ResourceDefinition.query.all()


def check_resource_published(resource_ids: List[str]) -> None:
    published_resources = [
        resource.resource_id for resource in get_published_resources()
    ]
    for resource_id in resource_ids:
        if resource_id not in published_resources:
            raise errors.KarpError(
                'Resource is not searchable: "{resource_id}"'.format(
                    resource_id=resource_id
                ),
                errors.ClientErrorCodes.RESOURCE_NOT_PUBLISHED,
            )


# def create_and_update_caches(id: str, version: int, config: Dict) -> None:
#     resource_models[id] = database.get_or_create_resource_model(config, version)
#     history_models[id] = database.get_or_create_history_model(id, version)
#     resource_versions[id] = version
#     resource_configs[id] = config
#     if "field_mapping" in config:
#         field_translations[id] = config["field_mapping"]


# def remove_from_caches(id: str) -> None:
#     del resource_models[id]
#     del history_models[id]
#     del resource_versions[id]
#     del resource_configs[id]
#     if id in field_translations:
#         del field_translations[id]


# def setup_resource_classes() -> None:
#     for resource in get_available_resources():
#         config = json.loads(resource.config_file)
#         create_and_update_caches(config["resource_id"], resource.version, config)


# def setup_resource_class(resource_id, version=None):
#     if version:
#         resource_def = database.get_resource_definition(resource_id, version)
#     else:
#         resource_def = database.get_active_resource_definition(resource_id)
#     if not resource_def:
#         raise ResourceNotFoundError(resource_id, version)
#     config = json.loads(resource_def.config_file)
#     create_and_update_caches(resource_id, resource_def.version, config)


# def _read_and_process_resources_from_dir(
#     config_dir: str, func
# ) -> List[Tuple[str, int]]:
#     files = [f for f in os.listdir(config_dir) if re.match(r".*\.json$", f)]
#     result = []
#     for filename in files:
#         print("Processing '{filename}' ...".format(filename=filename))
#         with open(os.path.join(config_dir, filename)) as fp:
#             result.append(func(fp, config_dir=config_dir))
#     return result


# def create_new_resource_from_dir(config_dir: str) -> List[Tuple[str, int]]:
#     return _read_and_process_resources_from_dir(config_dir, create_new_resource)


def create_new_resource_from_file(config_file: IO) -> Resource:
    return create_new_resource(config_file)

def create_resource_from_path(config: Path) -> List[Resource]:
    return []


# def update_resource_from_dir(config_dir: str) -> List[Tuple[str, int]]:
#     return _read_and_process_resources_from_dir(config_dir, update_resource)


# def update_resource_from_file(config_file: BinaryIO) -> Tuple[str, int]:
#     return update_resource(config_file)


def create_resource(
    cmd: commands.CreateResource,
    ctx: context.Context
):
    with ctx.resource_uow as uow:
        existing_resource = uow.resources.by_resource_id(cmd.resource_id)
        if existing_resource and existing_resource.id != cmd.id:
            raise errors.IntegrityError(
                f"Resource with '{cmd.resource_id}' already exists."
            )
        resource = model.Resource(
            entity_id=cmd.id,
            resource_id=cmd.resource_id,
            name=cmd.name,
            config=cmd.config,
            message=cmd.message,
            last_modified=cmd.timestamp,
            last_modified_by=cmd.created_by,
            entry_repository_type=cmd.entry_repository_type,
        )
        uow.resources.put(resource)
        uow.commit()



def create_new_resource(config_file: IO, config_dir=None) -> Resource:
    print("loading config with json ...")
    config = json.load(config_file)
    print("creating resource ...")
    resource = Resource.from_dict(config)

    print("resource created. setting up unit_of_work")
    with unit_of_work(using=ctx.resource_repo) as uw:
        print("adding resource to ctx.resource_repo ...")
        uw.put(resource)

    print("done! returning ...")
    return resource


#     config = load_and_validate_config(config_file)

#     resource_id = config["resource_id"]

#     version = database.get_next_resource_version(resource_id)

#     entry_json_schema = create_entry_json_schema(config)

#     config = load_plugins_to_config(config, version, config_dir)

#     resource = {
#         "resource_id": resource_id,
#         "version": version,
#         "config_file": json.dumps(config),
#         "entry_json_schema": json.dumps(entry_json_schema),
#     }

#     new_resource = database.ResourceDefinition(**resource)
#     db.session.add(new_resource)
#     db.session.commit()

#     sqlalchemyclass = database.get_or_create_resource_model(config, version)
#     history_model = database.get_or_create_history_model(resource_id, version)
#     sqlalchemyclass.__table__.create(bind=db.engine)
#     for child_class in sqlalchemyclass.child_tables.values():
#         child_class.__table__.create(bind=db.engine)
#     history_model.__table__.create(bind=db.engine)

#     return resource["resource_id"], resource["version"]


# def load_and_validate_config(config_file):
#     config = json.load(config_file)
#     try:
#         schema = get_resource_string("schema/resourceconf.schema.json")
#         validate_conf = fastjsonschema.compile(json.loads(schema))
#         validate_conf(config)
#     except fastjsonschema.JsonSchemaException as e:
#         raise ResourceInvalidConfigError(config["resource_id"], config_file, e.message)
#     return config


# def load_plugins_to_config(config: Dict, version, config_dir) -> Dict:
#     resource_id = config["resource_id"]

#     if "plugins" in config:
#         for plugin_id in config["plugins"]:
#             import karp.pluginmanager as plugins

#             if plugin_id not in plugins.plugins:
#                 raise PluginNotFoundError(plugin_id, resource_id)
#             for (field_name, field_conf) in plugins.plugins[
#                 plugin_id
#             ].resource_creation(resource_id, version, config_dir):
#                 config["fields"][field_name] = field_conf

#     return config


# def update_resource(config_file: BinaryIO, config_dir=None) -> Tuple[str, int]:
#     config = load_and_validate_config(config_file)

#     resource_id = config["resource_id"]
#     entry_json_schema = create_entry_json_schema(config)

#     resource_def = database.get_active_or_latest_resource_definition(resource_id)
#     if not resource_def:
#         raise RuntimeError(
#             "Could not find a resource_definition with id '{resource_id}".format(
#                 resource_id=resource_id
#             )
#         )
#     config = load_plugins_to_config(config, resource_def.version, config_dir)

#     config_diff = jsondiff.compare(json.loads(resource_def.config_file), config)
#     needs_reindex = False
#     not_allowed_change = False
#     not_allowed_changes = []
#     changes = []
#     for diff in config_diff:
#         print("config_diff = '{diff}'".format(diff=diff))
#         changes.append(diff)

#         if diff["type"] == "TYPECHANGE":
#             not_allowed_change = True
#             not_allowed_changes.append(diff)
#         elif diff["field"].endswith("required"):
#             continue
#         elif diff["field"] == "field_mapping":
#             continue
#         elif diff["type"] == "ADDED":
#             # TODO add rule for field_mappings
#             needs_reindex = True
#         elif diff["type"] == "REMOVED":
#             needs_reindex = True
#         elif diff["type"] == "CHANGE":
#             if diff["field"].endswith("type"):
#                 not_allowed_change = True
#                 not_allowed_changes.append(diff)
#             else:
#                 needs_reindex = True
#         else:
#             not_allowed_change = True
#             not_allowed_changes.append(diff)

#     # entry_json_schema_diff = jsondiff.compare(json.loads(resource_def.entry_json_schema), entry_json_schema)
#     # for diff in entry_json_schema_diff:
#     #     print("entry_json_schema_diff = '{diff}'".format(diff=diff))

#     if not config_diff:
#         return resource_id, None

#     if not_allowed_change:
#         raise ResourceConfigUpdateError(
#             """
#             You must 'create' a new version of '{resource_id}', current version '{version}'.
#             Changes = {not_allowed_changes}""".format(
#                 resource_id=resource_id,
#                 version=resource_def.version,
#                 not_allowed_changes=not_allowed_changes,
#             ),
#             resource_id,
#             config_file,
#         )
#     if needs_reindex:
#         print(
#             "You might need to reindex '{resource_id}' version '{version}'".format(
#                 resource_id=resource_id, version=resource_def.version
#             )
#         )
#     else:
#         print("Safe update.")
#     print("Changes:")
#     for diff in changes:
#         print(" - {diff}".format(diff=diff))
#     resource_def.config_file = json.dumps(config)
#     resource_def.entry_json_schema = json.dumps(entry_json_schema)
#     # db.session.update(resource_def)
#     db.session.commit()
#     if resource_def.active:
#         create_and_update_caches(resource_id, resource_def.version, config)

#     return resource_id, resource_def.version


def publish_resource(resource_id: str, version: Optional[int] = None):
    print(f"publish_resource resource_id='{resource_id}' ...")
    with unit_of_work(using=ctx.resource_repo) as uw:
        resource = uw.by_resource_id(resource_id)
        if resource.is_published:
            print(f"'{resource_id}' already published!")
            raise errors.ResourceAlreadyPublished(resource_id)
        resource.is_published = True
        resource.stamp(user="Local admin", message="Publishing")
        uw.update(resource)
    print("calling indexing.publish_index ...")
    indexing.publish_index(ctx.search_service, ctx.resource_repo, resource)
    print("index published")


#     resource = database.get_resource_definition(resource_id, version)
#     old_active = database.get_active_resource_definition(resource_id)
#     if old_active:
#         old_active.active = False
#     resource.active = True
#     db.session.commit()

#     config = json.loads(resource.config_file)
#     # this stuff doesn't matter right now since we are not modifying the state of the actual app, only the CLI
#     create_and_update_caches(resource_id, resource.version, config)


# def unpublish_resource(resource_id):
#     resource = database.get_active_resource_definition(resource_id)
#     if resource:
#         resource.active = False
#         db.session.update(resource)
#         db.session.commit()
#     remove_from_caches(resource_id)


# def delete_resource(resource_id, version):
#     resource = database.get_resource_definition(resource_id, version)
#     resource.deleted = True
#     resource.active = False
#     db.session.update(resource)
#     db.session.commit()


# def set_permissions(resource_id: str, version: int, permissions: Dict[str, bool]):
#     resource_def = database.get_resource_definition(resource_id, version)
#     config = json.loads(resource_def.config_file)
#     config["protected"] = permissions
#     resource_def.config_file = json.dumps(config)
#     # db.session.update(resource_def)
#     db.session.commit()


# def is_protected(resource_id, level):
#     """
#     Level can be READ, WRITE or ADMIN
#     """
#     resource = get_resource(resource_id)
#     protection = resource.config.get("protected", {})
#     return level == "WRITE" or level == "ADMIN" or protection.get("read")


# def get_all_metadata(resource_obj: Resource) -> Dict[str, EntryMetadata]:
#     history_table = resource_obj.history_model
#     result = db.session.query(
#         history_table.entry_id,
#         history_table.user_id,
#         history_table.timestamp,
#         func.max(history_table.version),
#     ).group_by(history_table.entry_id)
#     result_ = {
#         row[0]: EntryMetadata(row[1], last_modified=row[2], version=row[3])
#         for row in result
#     }
#     return result_


# def get_metadata(resource_def: Resource, _id: int) -> EntryMetadata:
#     history_table = resource_def.history_model
#     result = (
#         db.session.query(
#             history_table.user_id,
#             history_table.timestamp,
#             func.max(history_table.version),
#         )
#         .filter(history_table.entry_id == _id)
#         .group_by(history_table.entry_id)
#     )
#     return EntryMetadata(result[0][0], last_modified=result[0][1], version=result[0][2])
