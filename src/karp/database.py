import fastjsonschema  # pyre-ignore
import json

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

    for entry in entries:
        try:
            validate_entry(entry)
        except fastjsonschema.JsonSchemaException as e:
            raise RuntimeError(e)

        # TODO tmp fix for collections until we have decided how to handle them
        for field_name, field_val in entry.items():
            if isinstance(field_val, list):
                entry[field_name] = str(field_val)

        new_entry = cls(**entry)
        print(new_entry)
        db.session.add(new_entry)
    db.session.commit()


def delete_entry(resource, entry_id, version=None):
    cls = resource_classes[resource]
    entry = cls.query.filter_by(id=entry_id).first()
    db.session.delete(entry)
    db.session.commit()


def get_entry(resource, entry_id, version=None):
    cls = resource_classes[resource]
    entry = cls.query.filter_by(id=entry_id).first()
    return entry
