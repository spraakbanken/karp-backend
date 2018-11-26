import json
from flask import Blueprint                     # pyre-ignore
from flask import jsonify as flask_jsonify       # pyre-ignore
from flask import request                       # pyre-ignore
import karp.database as database


crud_api = Blueprint('crud_api', __name__)


@crud_api.route("/entries", methods=['GET'])
def get_entries():
    resource = request.args.get('resource')
    entries = database.get_entries(resource)
    # TODO don't parse json and then serialize it again
    return flask_jsonify([json.loads(entry.body) for entry in entries])


@crud_api.route("/entry", methods=['POST'])
def add_entry():
    """
    Example add: `curl -XPOST http://localhost:5000/entry?resource=places
                 -d '{"name": "Göteborg", "population": 3, "area": 30000}' -H "Content-Type: application/json"`
    """
    resource = request.args.get('resource')
    data = request.get_json()
    database.add_entry(resource, data)
    return flask_jsonify({'status': 'added'}), 201


@crud_api.route("/entry/<entry_id>", methods=['DELETE'])
def delete_entry(entry_id):
    resource = request.args.get('resource')
    database.delete_entry(resource, entry_id)
    return flask_jsonify({'status': 'removed'})


@crud_api.route("/entry/<entry_id>", methods=['GET'])
def get_entry(entry_id):
    resource = request.args.get('resource')
    entry = database.get_entry(resource, entry_id)
    # TODO don't parse json and then serialize it again
    return flask_jsonify(json.loads(entry.body))
