from typing import Optional, Dict, List
import json
import collections
import logging
from datetime import datetime, timezone

import fastjsonschema  # pyre-ignore
from sb_json_tools import jsondiff

# from karp.resourcemgr import get_resource
# from .resource import Resource


from karp.errors import (
    KarpError,
    ClientErrorCodes,
    EntryNotFoundError,
    UpdateConflict,
    EntryIdMismatch,
)

# from karp.database import db
# import karp.indexmgr as indexmgr
# import karp.resourcemgr.entrymetadata as entrymetadata
from karp.application import ctx

from karp.infrastructure.unit_of_work import unit_of_work


_logger = logging.getLogger("karp")


# def get_entries_by_column(resource_obj: Resource, filters):
#     config = resource_obj.config
#     cls = resource_obj.model
#     query = cls.query
#
#     joined_filters = []
#     simple_filters = {}
#
#     for filter_key in filters.keys():
#         tmp = collections.defaultdict(dict)
#         if filter_key in config["referenceable"] and config["fields"][filter_key].get(
#             "collection", False
#         ):
#             child_cls = cls.child_tables[filter_key]
#             tmp[child_cls.__tablename__][filter_key] = filters[filter_key]
#         else:
#             simple_filters[filter_key] = filters[filter_key]
#         joined_filters.extend(tmp.values())
#
#     query = query.filter_by(**simple_filters)
#
#     for child_filters in joined_filters:
#         child_cls = cls.child_tables[list(child_filters.keys())[0]]
#         query = query.join(child_cls).filter_by(**child_filters)
#
#     return [
#         {
#             "id": db_entry.id,
#             "entry_id": db_entry.entry_id,
#             "entry": json.loads(db_entry.body),
#         }
#         for db_entry in query
#     ]
#
#
# def get_entry(resource_id: str, entry_id: str, version: Optional[int] = None):
#     resource = get_resource(resource_id, version=version)
#     return get_entry_by_entry_id(resource, entry_id)
#
#
# def get_entry_by_entry_id(resource: Resource, entry_id: str):
#     cls = resource.model
#     return cls.query.filter_by(entry_id=entry_id).first()
#
#
# def diff(
#     resource_obj: Resource,
#     entry_id: str,
#     from_version: int = None,
#     to_version: int = None,
#     from_date: Optional[int] = None,
#     to_date: Optional[int] = None,
#     entry: Optional[Dict] = None,
# ):
#     src = resource_obj.model.query.filter_by(entry_id=entry_id).first()
#
#     query = resource_obj.history_model.query.filter_by(entry_id=src.id)
#     timestamp_field = resource_obj.history_model.timestamp
#
#     if from_version:
#         obj1_query = query.filter_by(version=from_version)
#     elif from_date is not None:
#         obj1_query = query.filter(timestamp_field >= from_date).order_by(
#             timestamp_field
#         )
#     else:
#         obj1_query = query.order_by(timestamp_field)
#     if to_version:
#         obj2_query = query.filter_by(version=to_version)
#     elif to_date is not None:
#         obj2_query = query.filter(timestamp_field <= to_date).order_by(
#             timestamp_field.desc()
#         )
#     else:
#         obj2_query = None
#
#     obj1 = obj1_query.first()
#     obj1_body = json.loads(obj1.body) if obj1 else None
#
#     if obj2_query:
#         obj2 = obj2_query.first()
#         obj2_body = json.loads(obj2.body) if obj2 else None
#     elif entry is not None:
#         obj2 = None
#         obj2_body = entry
#     else:
#         obj2 = query.order_by(timestamp_field.desc()).first()
#         obj2_body = json.loads(obj2.body) if obj2 else None
#
#     if not obj1_body or not obj2_body:
#         raise errors.KarpError("diff impossible!")
#
#     return (
#         jsondiff.compare(obj1_body, obj2_body),
#         obj1.version,
#         obj2.version if obj2 else None,
#     )
#
#
# def get_history(
#     resource_id: str,
#     user_id: Optional[str] = None,
#     entry_id: Optional[str] = None,
#     from_date: Optional[int] = None,
#     to_date: Optional[int] = None,
#     from_version: Optional[int] = None,
#     to_version: Optional[int] = None,
#     current_page: Optional[int] = 0,
#     page_size: Optional[int] = 100,
# ):
#     resource_obj = get_resource(resource_id)
#     timestamp_field = resource_obj.history_model.timestamp
#     query = resource_obj.history_model.query
#     if user_id:
#         query = query.filter_by(user_id=user_id)
#     if entry_id:
#         current_entry = resource_obj.model.query.filter_by(entry_id=entry_id).first()
#         query = query.filter_by(entry_id=current_entry.id)
#
#     version_field = resource_obj.history_model.version
#     if entry_id and from_version:
#         query = query.filter(version_field >= from_version)
#     elif from_date is not None:
#         query = query.filter(timestamp_field >= from_date)
#     if entry_id and to_version:
#         query = query.filter(version_field < to_version)
#     elif to_date is not None:
#         query = query.filter(timestamp_field <= to_date)
#
#     paged_query = query.limit(page_size).offset(current_page * page_size)
#     total = query.count()
#
#     result = []
#     for history_entry in paged_query:
#         # TODO fix this, entry_id in history refers to the "normal" id in non-history table
#         entry_id = (
#             resource_obj.model.query.filter_by(id=history_entry.entry_id)
#             .first()
#             .entry_id
#         )
#         # TODO fix this, we should get the diff in another way, probably store the diffs directly in the database
#         entry_version = history_entry.version
#         if entry_version > 1:
#             previous_body = json.loads(
#                 resource_obj.history_model.query.filter_by(
#                     entry_id=history_entry.entry_id, version=entry_version - 1
#                 )
#                 .first()
#                 .body
#             )
#         else:
#             previous_body = {}
#         history_diff = jsondiff.compare(previous_body, json.loads(history_entry.body))
#         result.append(
#             {
#                 "timestamp": history_entry.timestamp,
#                 "message": history_entry.message if history_entry.message else "",
#                 "entry_id": entry_id,
#                 "version": entry_version,
#                 "op": history_entry.op,
#                 "user_id": history_entry.user_id,
#                 "diff": history_diff,
#             }
#         )
#
#     return result, total
#
#
# def get_entry_history(resource_id, entry_id, version):
#     resource_obj = get_resource(resource_id)
#     db_id = resource_obj.model.query.filter_by(entry_id=entry_id).first().id
#     result = resource_obj.history_model.query.filter_by(
#         entry_id=db_id, version=version
#     ).first()
#     return {
#         "id": entry_id,
#         "resource": resource_id,
#         "version": version,
#         "entry": json.loads(result.body),
#         "last_modified_by": result.user_id,
#         "last_modified": result.timestamp,
#     }
#
#
def add_entry(
    resource_id: str,
    entry: Dict,
    user_id: str,
    message: str = None,
    resource_version: int = None,
):
    return add_entries(
        resource_id,
        [entry],
        user_id,
        message=message,
        resource_version=resource_version,
    )[0]


#
# def preview_entry(resource_id, entry, resource_version=None):
#     resource = get_resource(resource_id, version=resource_version)
#     entry_json = _validate_and_prepare_entry(resource, entry)
#     return entry_json


def update_entry(
    resource_id: str,
    entry_id: str,
    version: int,
    entry: Dict,
    user_id: str,
    message: str = None,
    resource_version: int = None,
    force: bool = False,
) -> str:
    with unit_of_work(using=ctx.resource_repo) as uw:
        resource = uw.get_active_resource(resource_id)
    #     resource = get_resource(resource_id, version=resource_version)

    schema = _compile_schema(resource.entry_json_schema)
    _validate_entry(schema, entry)

    with unit_of_work(using=resource.entry_repository) as uw:
        current_db_entry = uw.by_entry_id(entry_id)

        #     current_db_entry = resource.model.query.filter_by(
        #         entry_id=entry_id, deleted=False
        #     ).first()
        if not current_db_entry:
            raise EntryNotFoundError(
                resource_id,
                entry_id,
                entry_version=version,
                resource_version=resource_version,
            )

        diff = jsondiff.compare(current_db_entry.body, entry)
        if not diff:
            raise KarpError("No changes made", ClientErrorCodes.ENTRY_NOT_CHANGED)

        #     db_entry_json = json.dumps(entry)
        #     db_id = current_db_entry.id
        #     latest_history_entry = (
        #         resource.history_model.query.filter_by(entry_id=db_id)
        #         .order_by(resource.history_model.version.desc())
        #         .first()
        #     )
        print(f"({current_db_entry.version}, {version})")
        if not force and current_db_entry.version != version:
            print("version conflict")
            raise UpdateConflict(diff)

        new_entry = resource.create_entry_from_dict(
            entry, user=user_id, message=message
        )

        if new_entry.entry_id != entry_id:
            raise EntryIdMismatch(new_entry.entry_id, entry_id)

        uw.update(new_entry)

    return new_entry.entry_id


# def update_entry(
#     resource_id: str,
#     entry_id: str,
#     version: int,
#     entry: Dict,
#     user_id: str,
#     message: str = None,
#     resource_version: int = None,
#     force: bool = False,
# ):
#     resource = get_resource(resource_id, version=resource_version)
#
#     schema = _compile_schema(resource.entry_json_schema)
#     _validate_entry(schema, entry)
#
#     current_db_entry = resource.model.query.filter_by(
#         entry_id=entry_id, deleted=False
#     ).first()
#     if not current_db_entry:
#         raise EntryNotFoundError(
#             resource_id,
#             entry_id,
#             entry_version=version,
#             resource_version=resource_version,
#         )
#
#     diff = jsondiff.compare(json.loads(current_db_entry.body), entry)
#     if not diff:
#         raise KarpError("No changes made", ClientErrorCodes.ENTRY_NOT_CHANGED)
#
#     db_entry_json = json.dumps(entry)
#     db_id = current_db_entry.id
#     latest_history_entry = (
#         resource.history_model.query.filter_by(entry_id=db_id)
#         .order_by(resource.history_model.version.desc())
#         .first()
#     )
#     if not force and latest_history_entry.version > version:
#         raise UpdateConflict(diff)
#     history_entry = resource.history_model(
#         entry_id=db_id,
#         user_id=user_id,
#         body=db_entry_json,
#         version=latest_history_entry.version + 1,
#         op="UPDATE",
#         message=message,
#         timestamp=datetime.now(timezone.utc).timestamp(),
#     )
#
#     kwargs = _src_entry_to_db_kwargs(
#         entry, db_entry_json, resource.model, resource.config
#     )
#     if resource.active and str(kwargs["entry_id"]) != current_db_entry.entry_id:
#         indexmgr.delete_entry(resource_id, current_db_entry.entry_id)
#     for key, value in kwargs.items():
#         setattr(current_db_entry, key, value)
#
#     db.session.add(history_entry)
#     db.session.commit()
#
#     if resource.active:
#         index_entry_json = _src_entry_to_index_entry(resource, entry)
#         indexmgr.add_entries(
#             resource_id,
#             [
#                 (
#                     current_db_entry.entry_id,
#                     entrymetadata.EntryMetadata.init_from_model(history_entry),
#                     index_entry_json,
#                 )
#             ],
#         )
#     return current_db_entry.entry_id
#
#
# def add_entries_from_file(resource_id: str, version: int, data: str) -> int:
#     with open(data) as fp:
#         objs = []
#         for line in fp:
#             objs.append(json.loads(line))
#         add_entries(resource_id, objs, user_id="local_admin", resource_version=version)
#     return len(objs)


def add_entries(
    resource_id: str,
    entries: List[Dict],
    user_id: str,
    message: str = None,
    resource_version: int = None,
):
    """
    Add entries to DB and INDEX (if present and resource is active).

    Raises
    ------
    RuntimeError
        If the resource.entry_json_schema fails to compile.
    KarpError
        - If an entry fails to be validated against the json schema.
        - If the DB interaction fails.

    Returns
    -------
    List
        List of the id's of the created entries.
    """
    if not isinstance(resource_id, str):
        raise ValueError(
            f"'resource_id' must be of type 'str', were '{type(resource_id)}'"
        )
    with unit_of_work(using=ctx.resource_repo) as uw:
        resource = uw.get_active_resource(resource_id)

    # resource = get_resource(resource_id, version=resource_version)
    # resource_conf = resource.config

    validate_entry = _compile_schema(resource.entry_json_schema)

    created_db_entries = []
    with unit_of_work(using=resource.entry_repository) as uw:
        for entry_raw in entries:
            _validate_entry(validate_entry, entry_raw)

            entry = resource.create_entry_from_dict(
                entry_raw, user=user_id, message=message
            )
            print("before uw.put")
            uw.put(entry)
            created_db_entries.append(entry.entry_id)
            print("after uw.put")
    print("after db commit")
    return created_db_entries


# def add_entries(
#     resource_id: str,
#     entries: List[Dict],
#     user_id: str,
#     message: str = None,
#     resource_version: int = None,
# ):
#     """
#     Add entries to DB and INDEX (if present and resource is active).
#
#     Raises
#     ------
#     RuntimeError
#         If the resource.entry_json_schema fails to compile.
#     KarpError
#         - If an entry fails to be validated against the json schema.
#         - If the DB interaction fails.
#
#     Returns
#     -------
#     List
#         List of the id's of the created entries.
#     """
#     resource = get_resource(resource_id, version=resource_version)
#     resource_conf = resource.config
#
#     validate_entry = _compile_schema(resource.entry_json_schema)
#
#     try:
#         created_db_entries = []
#         for entry in entries:
#             _validate_entry(validate_entry, entry)
#
#             entry_json = json.dumps(entry)
#             db_entry = _src_entry_to_db_entry(
#                 entry, entry_json, resource.model, resource_conf
#             )
#             created_db_entries.append((db_entry, entry, entry_json))
#             db.session.add(db_entry)
#
#         db.session.commit()
#
#         created_history_entries = []
#         for db_entry, entry, entry_json in created_db_entries:
#             history_entry = resource.history_model(
#                 entry_id=db_entry.id,
#                 user_id=user_id,
#                 body=entry_json,
#                 version=1,
#                 op="ADD",
#                 message=message,
#                 timestamp=datetime.now(timezone.utc).timestamp(),
#             )
#             created_history_entries.append((db_entry, entry, history_entry))
#             db.session.add(history_entry)
#         db.session.commit()
#     except sql_exception.IntegrityError as e:
#         _logger.exception("IntegrityError")
#         print("e = {e!r}".format(e=e))
#         print("e.orig.args = {e!r}".format(e=e.orig.args))
#         raise KarpError(
#             "Database error: {msg}".format(msg=e.orig.args),
#             ClientErrorCodes.DB_INTEGRITY_ERROR,
#         )
#     except sql_exception.SQLAlchemyError as e:
#         _logger.exception("Adding entries to DB failed.")
#         print("e = {e!r}".format(e=e))
#         raise KarpError(
#             "Database error: {msg}".format(msg=e.msg), ClientErrorCodes.DB_GENERAL_ERROR
#         )
#
#     if resource.active:
#         indexmgr.add_entries(
#             resource_id,
#             [
#                 (
#                     db_entry.entry_id,
#                     entrymetadata.EntryMetadata.init_from_model(history_entry),
#                     _src_entry_to_index_entry(resource, entry),
#                 )
#                 for db_entry, entry, history_entry in created_history_entries
#             ],
#         )
#
#     return [db_entry.entry_id for db_entry, _, _ in created_db_entries]
#
#
# def _src_entry_to_db_entry(entry, entry_json, resource_model, resource_conf):
#     kwargs = _src_entry_to_db_kwargs(entry, entry_json, resource_model, resource_conf)
#     db_entry = resource_model(**kwargs)
#     return db_entry
#
#
# def _src_entry_to_db_kwargs(entry, entry_json, resource_model, resource_conf):
#     kwargs = {"body": entry_json}
#
#     for field_name in resource_conf.get("referenceable", ()):
#         field_val = entry.get(field_name)
#         if resource_conf["fields"][field_name].get("collection", False):
#             child_table = resource_model.child_tables[field_name]
#             for elem in field_val:
#                 if field_name not in kwargs:
#                     kwargs[field_name] = []
#                 kwargs[field_name].append(child_table(**{field_name: elem}))
#         else:
#             if field_val:
#                 kwargs[field_name] = field_val
#     id_field = resource_conf.get("id")
#     if id_field:
#         kwargs["entry_id"] = entry[id_field]
#     else:
#         kwargs["entry_id"] = "TODO"  # generate id for resources that are missing it
#     return kwargs


def delete_entry(resource_id: str, entry_id: str, user_id: str):
    with unit_of_work(using=ctx.resource_repo) as uw:
        resource = uw.get_active_resource(resource_id)

    with unit_of_work(using=resource.entry_repository) as uw:
        entry = uw.by_entry_id(entry_id)

        #     resource = get_resource(resource_id)
        #     entry = resource.model.query.filter_by(entry_id=entry_id, deleted=False).first()
        if not entry:
            raise EntryNotFoundError(resource_id, entry_id)

        entry.discard(user=user_id)
        uw.update(entry)


# def delete_entry(resource_id: str, entry_id: str, user_id: str):
#     resource = get_resource(resource_id)
#     entry = resource.model.query.filter_by(entry_id=entry_id, deleted=False).first()
#     if not entry:
#         raise EntryNotFoundError(resource_id, entry_id)
#     entry.deleted = True
#     history_cls = resource.history_model
#     history_entry = history_cls(
#         entry_id=entry.id,
#         user_id=user_id,
#         op="DELETE",
#         version=-1,
#         timestamp=datetime.now(timezone.utc).timestamp(),
#     )
#     db.session.add(history_entry)
#     db.session.commit()
#     indexmgr.delete_entry(resource_id, entry.entry_id)
#
#
# def _src_entry_to_index_entry(resource: Resource, src_entry: Dict):
#     """
#     Make a "src entry" into an "index entry"
#     """
#     return indexmgr.transform_to_index_entry(
#         resource, src_entry, resource.config["fields"].items()
#     )
#
#
# def _validate_and_prepare_entry(resource, entry):
#     validate_entry = _compile_schema(resource.entry_json_schema)
#     _validate_entry(validate_entry, entry)
#     return _src_entry_to_index_entry(resource, entry)


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
        _logger.warning(
            "Entry not valid:\n{entry}\nMessage: {message}".format(
                entry=json.dumps(json_obj, indent=2), message=e.message
            )
        )
        raise KarpError("entry not valid", ClientErrorCodes.ENTRY_NOT_VALID)
