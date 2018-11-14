from typing import Tuple

from .models import db, Entry


def get_entries():
    entries = Entry.query.all()
    return entries


def add_entry(value):
    entry = Entry(value=value)
    db.session.add(entry)
    db.session.commit()


def delete_entry(value):
    entry = Entry.query.filter_by(value=value).first()
    db.session.delete(entry)
    db.session.commit()


def get_entry(value):
    entry = Entry.query.filter_by(value=value).first()
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
