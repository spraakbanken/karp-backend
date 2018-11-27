from flask import current_app
from typing import Tuple
import fastjsonschema  # pyre-ignore
import json
import elasticsearch.helpers

from .models import resource_classes, Resource
from karp import db


def get_entries(resource, version=None):
    cls = resource_classes[resource]
    entries = cls.query.all()
    return entries


def add_entry(resource_id, entry):
    # TOO add to which version?
    resource_def = Resource.query.filter_by(resource_id=resource_id, active=True).first()
    version = resource_def.version
    add_entries(resource_id, version, [entry])


def add_entries(resource_id, version, entries):
    cls = resource_classes[resource_id]

    resource_def = Resource.query.filter_by(resource_id=resource_id, version=version).first()
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

    if not current_app.elasticsearch:
        return

    index_to_es = []
    for (db_entry, entry) in created_db_entries:
        index_to_es.append({
            '_index': resource_id + '_' + str(version),
            '_id': db_entry.id,
            '_type': 'entry',
            '_source': entry
        })

    elasticsearch.helpers.bulk(current_app.elasticsearch, index_to_es)


def delete_entry(resource, entry_id, version=None):
    cls = resource_classes[resource]
    entry = cls.query.filter_by(id=entry_id).first()
    db.session.delete(entry)
    db.session.commit()


def get_entry(resource, entry_id, version=None):
    cls = resource_classes[resource]
    entry = cls.query.filter_by(id=entry_id).first()
    return entry


def check_database_status() -> Tuple[bool, str]:
    is_database_working = True
    output = 'database is ok'

    try:
        # to check database we will execute raw query
        db.engine.execute('SELECT 1')
    except Exception as e:
        output = str(e)
        is_database_working = False

    return is_database_working, output
