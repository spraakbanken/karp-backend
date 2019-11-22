from typing import Optional, Dict
import json
import collections

from sb_json_tools import jsondiff

from karp.resourcemgr import get_resource
from .resource import Resource
import karp.errors as errors


def get_entries_by_column(resource_obj: Resource, filters):
    config = resource_obj.config
    cls = resource_obj.model
    query = cls.query

    joined_filters = []
    simple_filters = {}

    for filter_key in filters.keys():
        tmp = collections.defaultdict(dict)
        if filter_key in config["referenceable"] and config["fields"][filter_key].get(
            "collection", False
        ):
            child_cls = cls.child_tables[filter_key]
            tmp[child_cls.__tablename__][filter_key] = filters[filter_key]
        else:
            simple_filters[filter_key] = filters[filter_key]
        joined_filters.extend(tmp.values())

    query = query.filter_by(**simple_filters)

    for child_filters in joined_filters:
        child_cls = cls.child_tables[list(child_filters.keys())[0]]
        query = query.join(child_cls).filter_by(**child_filters)

    return [
        {
            "id": db_entry.id,
            "entry_id": db_entry.entry_id,
            "entry": json.loads(db_entry.body),
        }
        for db_entry in query
    ]


def get_entry(resource_id: str, entry_id: str, version: Optional[int] = None):
    resource = get_resource(resource_id, version=version)
    return get_entry_by_entry_id(resource, entry_id)


def get_entry_by_entry_id(resource: Resource, entry_id: str):
    cls = resource.model
    return cls.query.filter_by(entry_id=entry_id).first()


def diff(
    resource_obj: Resource,
    entry_id: str,
    from_version: int = None,
    to_version: int = None,
    from_date: Optional[int] = None,
    to_date: Optional[int] = None,
    entry: Optional[Dict] = None,
):
    src = resource_obj.model.query.filter_by(entry_id=entry_id).first()

    query = resource_obj.history_model.query.filter_by(entry_id=src.id)
    timestamp_field = resource_obj.history_model.timestamp

    if from_version:
        obj1_query = query.filter_by(version=from_version)
    elif from_date is not None:
        obj1_query = query.filter(timestamp_field >= from_date).order_by(
            timestamp_field
        )
    else:
        obj1_query = query.order_by(timestamp_field)
    if to_version:
        obj2_query = query.filter_by(version=to_version)
    elif to_date is not None:
        obj2_query = query.filter(timestamp_field <= to_date).order_by(
            timestamp_field.desc()
        )
    else:
        obj2_query = None

    obj1 = obj1_query.first()
    obj1_body = json.loads(obj1.body) if obj1 else None

    if obj2_query:
        obj2 = obj2_query.first()
        obj2_body = json.loads(obj2.body) if obj2 else None
    elif entry is not None:
        obj2 = None
        obj2_body = entry
    else:
        obj2 = query.order_by(timestamp_field.desc()).first()
        obj2_body = json.loads(obj2.body) if obj2 else None

    if not obj1_body or not obj2_body:
        raise errors.KarpError("diff impossible!")

    return (
        jsondiff.compare(obj1_body, obj2_body),
        obj1.version,
        obj2.version if obj2 else None,
    )


def get_history(
    resource_id: str,
    user_id: Optional[str] = None,
    entry_id: Optional[str] = None,
    from_date: Optional[int] = None,
    to_date: Optional[int] = None,
    from_version: Optional[int] = None,
    to_version: Optional[int] = None,
    current_page: Optional[int] = 0,
    page_size: Optional[int] = 100,
):
    resource_obj = get_resource(resource_id)
    timestamp_field = resource_obj.history_model.timestamp
    query = resource_obj.history_model.query
    if user_id:
        query = query.filter_by(user_id=user_id)
    if entry_id:
        current_entry = resource_obj.model.query.filter_by(entry_id=entry_id).first()
        query = query.filter_by(entry_id=current_entry.id)

    version_field = resource_obj.history_model.version
    if entry_id and from_version:
        query = query.filter(version_field >= from_version)
    elif from_date is not None:
        query = query.filter(timestamp_field >= from_date)
    if entry_id and to_version:
        query = query.filter(version_field < to_version)
    elif to_date is not None:
        query = query.filter(timestamp_field <= to_date)

    paged_query = query.limit(page_size).offset(current_page * page_size)
    total = query.count()

    result = []
    for history_entry in paged_query:
        # TODO fix this, entry_id in history refers to the "normal" id in non-history table
        entry_id = (
            resource_obj.model.query.filter_by(id=history_entry.entry_id)
            .first()
            .entry_id
        )
        # TODO fix this, we should get the diff in another way, probably store the diffs directly in the database
        entry_version = history_entry.version
        if entry_version > 1:
            previous_body = json.loads(
                resource_obj.history_model.query.filter_by(
                    entry_id=history_entry.entry_id, version=entry_version - 1
                )
                .first()
                .body
            )
        else:
            previous_body = {}
        history_diff = jsondiff.compare(previous_body, json.loads(history_entry.body))
        result.append(
            {
                "timestamp": history_entry.timestamp,
                "message": history_entry.message if history_entry.message else "",
                "entry_id": entry_id,
                "version": entry_version,
                "op": history_entry.op,
                "user_id": history_entry.user_id,
                "diff": history_diff,
            }
        )

    return result, total


def get_entry_history(resource_id, entry_id, version):
    resource_obj = get_resource(resource_id)
    db_id = resource_obj.model.query.filter_by(entry_id=entry_id).first().id
    result = resource_obj.history_model.query.filter_by(
        entry_id=db_id, version=version
    ).first()
    return {
        "id": entry_id,
        "resource": resource_id,
        "version": version,
        "entry": json.loads(result.body),
        "last_modified_by": result.user_id,
        "last_modified": result.timestamp,
    }
