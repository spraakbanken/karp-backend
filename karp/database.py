from flask_sqlalchemy import SQLAlchemy
from .web import app


db = SQLAlchemy(app)
from .models import *
# temporary setup of tables
db.create_all()


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
