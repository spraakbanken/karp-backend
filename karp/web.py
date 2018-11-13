import flask
from flask import Blueprint, request
import karp.database as database


karp_api = Blueprint('karp_api', __name__)


@karp_api.route("/entries", methods=['GET'])
def get_entries():
    resource = request.args.get('resource')
    entries = database.get_entries(resource)
    return flask.jsonify([entry.serialize() for entry in entries])


@karp_api.route("/entry", methods=['POST'])
def add_entry():
    """
    Example add: `curl -XPOST http://localhost:5000/entry?resource=places
                 -d '{"name": "Göteborg", "population": 3, "area": 30000}' -H "Content-Type: application/json"`
    """
    resource = request.args.get('resource')
    data = request.get_json()
    database.add_entry(resource, data)
    return flask.jsonify({'status': 'added'}), 201


@karp_api.route("/entry/<entry_id>", methods=['DELETE'])
def delete_entry(entry_id):
    resource = request.args.get('resource')
    database.delete_entry(resource, entry_id)
    return flask.jsonify({'status': 'removed'})


@karp_api.route("/entry/<entry_id>", methods=['GET'])
def get_entry(entry_id):
    resource = request.args.get('resource')
    entry = database.get_entry(resource, entry_id)
    return flask.jsonify(entry.serialize())
