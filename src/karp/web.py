import flask
from flask import Blueprint
import karp.database as database


karp_api = Blueprint('karp_api', __name__)


@karp_api.route("/entries", methods=['GET'])
def get_entries():
    entries = database.get_entries()
    return flask.jsonify([entry.serialize for entry in entries])


@karp_api.route("/entry/<value>", methods=['POST'])
def add_entry(value):
    database.add_entry(value)
    return flask.jsonify({'status': 'added'}), 201


@karp_api.route("/entry/<value>", methods=['DELETE'])
def delete_entry(value):
    database.delete_entry(value)
    return flask.jsonify({'status': 'removed'})


@karp_api.route("/entry/<value>", methods=['GET'])
def get_entry(value):
    entry = database.get_entry(value)
    return flask.jsonify(entry.serialize)
