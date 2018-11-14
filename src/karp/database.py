from typing import Tuple

from .models import db, resource_classes


def get_entries(resource, version=None):
    cls = resource_classes[resource]
    entries = cls.query.all()
    return entries


def add_entry(resource, entry, version=None):
    cls = resource_classes[resource]

    # TODO get schema for this resource and validate entry

    new_entry = cls(**entry)
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
