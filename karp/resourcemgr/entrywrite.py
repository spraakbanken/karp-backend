import json
import fastjsonschema  # pyre-ignore
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Iterable, Optional

from sqlalchemy import exc as sql_exception

from sb_json_tools import jsondiff
import json_streams

from karp.errors import (
    KarpError,
    ClientErrorCodes,
    EntryNotFoundError,
    UpdateConflict,
    ResourceNotFoundError,
    ValidationError,
)
from karp.resourcemgr import get_resource
from karp.database import db
import karp.indexmgr as indexmgr
from .resource import Resource
import karp.resourcemgr.entrymetadata as entrymetadata

_logger = logging.getLogger("karp")


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


def preview_entry(resource_id, entry, resource_version=None):
    resource = get_resource(resource_id, version=resource_version)
    return _validate_and_prepare_entry(resource, entry)


def update_entries(
    resource_id: str,
    entries: Iterable[Dict],
    *,
    user_id: str,
    message: str,
    resource_version: Optional[int] = None
) -> Dict[str, List]:
    result = {
        "success": [],
        "failure": [],
    }
    for obj in entries:
        try:
            succ_id = update_entry(
                resource_id=resource_id,
                entry_id=obj["entry_id"],
                version=obj.get("version", 0),
                entry=obj["entry"],
                user_id=user_id,
                message=message,
                resource_version=resource_version,
                force=True,
            )
            result["success"].append(succ_id)
        except ResourceNotFoundError:
            raise
        except KarpError as exc:
            result["failure"].append(
                {
                    "entry": obj,
                    "error": exc.message,
                }
            )
    return result


def update_entry(
    resource_id: str,
    entry_id: str,
    version: int,
    entry: Dict,
    user_id: str,
    message: str = None,
    resource_version: int = None,
    force: bool = False,
):
    resource = get_resource(resource_id, version=resource_version)

    schema = _compile_schema(resource.entry_json_schema)
    _validate_entry(schema, entry)

    current_db_entry = resource.model.query.filter_by(
        entry_id=entry_id, deleted=False
    ).first()
    if not current_db_entry:
        raise EntryNotFoundError(
            resource_id,
            entry_id,
            entry_version=version,
            resource_version=resource_version,
        )

    diff = jsondiff.compare(json.loads(current_db_entry.body), entry)
    if not diff:
        raise KarpError("No changes made", ClientErrorCodes.ENTRY_NOT_CHANGED)

    db_entry_json = json.dumps(entry)
    db_id = current_db_entry.id
    latest_history_entry = (
        resource.history_model.query.filter_by(entry_id=db_id)
        .order_by(resource.history_model.version.desc())
        .first()
    )
    if not force and latest_history_entry.version > version:
        raise UpdateConflict(diff)
    history_entry = resource.history_model(
        entry_id=db_id,
        user_id=user_id,
        body=db_entry_json,
        version=latest_history_entry.version + 1,
        op="UPDATE",
        message=message,
        timestamp=datetime.now(timezone.utc).timestamp(),
    )

    kwargs = _src_entry_to_db_kwargs(
        entry, db_entry_json, resource.model, resource.config
    )
    if resource.active and str(kwargs["entry_id"]) != current_db_entry.entry_id:
        indexmgr.delete_entry(resource_id, current_db_entry.entry_id)
    for key, value in kwargs.items():
        setattr(current_db_entry, key, value)

    db.session.add(history_entry)
    db.session.commit()

    if resource.active:
        index_entry_json = _src_entry_to_index_entry(resource, entry)
        indexmgr.add_entries(
            resource_id,
            [
                (
                    current_db_entry.entry_id,
                    entrymetadata.EntryMetadata.init_from_model(history_entry),
                    index_entry_json,
                )
            ],
        )
    return current_db_entry.entry_id


def add_entries_from_file(resource_id: str, version: int, data: Path) -> List[str]:
    return add_entries(
        resource_id,
        json_streams.load_from_file(data),
        user_id="local_admin",
        resource_version=version,
    )


def add_entries(
    resource_id: str,
    entries: Iterable[Dict],
    user_id: str,
    message: str = None,
    resource_version: int = None,
) -> List[str]:
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
    resource = get_resource(resource_id, version=resource_version)
    resource_conf = resource.config

    validate_entry = _compile_schema(resource.entry_json_schema)

    try:
        created_db_entries = []
        for entry in entries:
            _validate_entry(validate_entry, entry)

            entry_json = json.dumps(entry)
            db_entry = _src_entry_to_db_entry(
                entry, entry_json, resource.model, resource_conf
            )
            created_db_entries.append((db_entry, entry, entry_json))
            db.session.add(db_entry)

        db.session.commit()

        created_history_entries = []
        for db_entry, entry, entry_json in created_db_entries:
            history_entry = resource.history_model(
                entry_id=db_entry.id,
                user_id=user_id,
                body=entry_json,
                version=1,
                op="ADD",
                message=message,
                timestamp=datetime.now(timezone.utc).timestamp(),
            )
            created_history_entries.append((db_entry, entry, history_entry))
            db.session.add(history_entry)
        db.session.commit()
    except sql_exception.IntegrityError as e:
        _logger.exception("IntegrityError")
        print("e = {e!r}".format(e=e))
        print("e.orig.args = {e!r}".format(e=e.orig.args))
        raise KarpError(
            "Database error: {msg}".format(msg=e.orig.args),
            ClientErrorCodes.DB_INTEGRITY_ERROR,
        )
    except sql_exception.SQLAlchemyError as e:
        _logger.exception("Adding entries to DB failed.")
        print("e = {e!r}".format(e=e))
        raise KarpError(
            "Database error: {msg}".format(msg=e.msg), ClientErrorCodes.DB_GENERAL_ERROR
        )

    if resource.active:
        indexmgr.add_entries(
            resource_id,
            [
                (
                    db_entry.entry_id,
                    entrymetadata.EntryMetadata.init_from_model(history_entry),
                    _src_entry_to_index_entry(resource, entry),
                )
                for db_entry, entry, history_entry in created_history_entries
            ],
        )

    return [db_entry.entry_id for db_entry, _, _ in created_db_entries]


def _src_entry_to_db_entry(entry, entry_json, resource_model, resource_conf):
    kwargs = _src_entry_to_db_kwargs(entry, entry_json, resource_model, resource_conf)
    return resource_model(**kwargs)


def _src_entry_to_db_kwargs(entry, entry_json, resource_model, resource_conf):
    kwargs = {"body": entry_json}

    for field_name in resource_conf.get("referenceable", ()):
        field_val = entry.get(field_name)
        if resource_conf["fields"][field_name].get("collection", False):
            child_table = resource_model.child_tables[field_name]
            for elem in field_val:
                if field_name not in kwargs:
                    kwargs[field_name] = []
                kwargs[field_name].append(child_table(**{field_name: elem}))
        else:
            if field_val:
                kwargs[field_name] = field_val
    id_field = resource_conf.get("id")
    if id_field:
        kwargs["entry_id"] = entry[id_field]
    else:
        kwargs["entry_id"] = "TODO"  # generate id for resources that are missing it
    return kwargs


def delete_entries(
    resource_id: str,
    entry_ids: Iterable[str],
    user_id: str,  # resource_version: int
) -> Dict[str, List]:
    result = {
        "success": [],
        "failure": [],
    }
    for entry_id in entry_ids:
        try:
            succ_id = delete_entry(
                resource_id=resource_id,
                entry_id=entry_id,
                user_id=user_id,
                # resource_version=resource_version,
            )
            result["success"].append(succ_id)
        except ResourceNotFoundError:
            raise
        except KarpError as exc:
            result["failure"].append(
                {
                    "entry_id": entry_id,
                    "error": exc.message,
                }
            )
    return result


def delete_entry(resource_id: str, entry_id: str, user_id: str):
    resource = get_resource(resource_id)
    entry = resource.model.query.filter_by(entry_id=entry_id, deleted=False).first()
    if not entry:
        raise EntryNotFoundError(resource_id, entry_id)
    entry.deleted = True
    history_cls = resource.history_model
    history_entry = history_cls(
        entry_id=entry.id,
        user_id=user_id,
        op="DELETE",
        version=-1,
        timestamp=datetime.now(timezone.utc).timestamp(),
    )
    db.session.add(history_entry)
    db.session.commit()
    indexmgr.delete_entry(resource_id, entry.entry_id)


def _src_entry_to_index_entry(resource: Resource, src_entry: Dict):
    """
    Make a "src entry" into an "index entry"
    """
    return indexmgr.transform_to_index_entry(
        resource, src_entry, resource.config["fields"].items()
    )


def _validate_and_prepare_entry(resource, entry):
    validate_entry = _compile_schema(resource.entry_json_schema)
    _validate_entry(validate_entry, entry)
    return _src_entry_to_index_entry(resource, entry)


def _compile_schema(json_schema):
    try:
        return fastjsonschema.compile(json_schema)
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
        raise ValidationError("entry not valid", err=e, obj=json_obj) from e
