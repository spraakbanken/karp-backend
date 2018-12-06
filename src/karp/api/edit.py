from flask import Blueprint                     # pyre-ignore
from flask import jsonify as flask_jsonify       # pyre-ignore
from flask import request  # pyre-ignore

import karp.resourcemgr as resourcemgr


edit_api = Blueprint('edit_api', __name__)

"""

    <resource>/delete/<id> DELETE
    <resource>/add POST alt. <resource>/add_without_message POST
        data: { object }
    <resource>/add_with_message POST alt. <resource>/add POST
        data: { 'doc': { object }, 'message': "" }
    <resource>/update/<id> POST
        data: { 'doc': ..., 'version': "", 'message': "" }

"""


@edit_api.route("/<resource_id>/add", methods=['POST'])
def add_entry(resource_id):
    """
    Example add: `curl -XPOST http://localhost:5000/entry?resource=places
                 -d '{"name": "Göteborg", "population": 3, "area": 30000}' -H "Content-Type: application/json"`
    """
    data = request.get_json()
    new_id = resourcemgr.add_entry(resource_id, data)
    return flask_jsonify({'status': 'added', 'newID': new_id}), 201


@edit_api.route("/<resource_id>/add_with_message", methods=['POST'])
def add_entry_with_msg(resource_id):
    """
    Example add: `curl -XPOST http://localhost:5000/entry?resource=places
                 -d '{"name": "Göteborg", "population": 3, "area": 30000}' -H "Content-Type: application/json"`
    """
    data = request.get_json()
    new_id = resourcemgr.add_entry(resource_id, data['doc'], message=data['message'])
    return flask_jsonify({'status': 'added', 'newID': new_id}), 201


@edit_api.route("/<resource_id>/_all")
def get_all_entries(resource_id):
    """
    TODO replace using this with /query call without a query
    """
    entries = resourcemgr.get_entries(resource_id)
    return flask_jsonify(entries)


@edit_api.route("/<resource_id>/delete/<entry_id>", methods=['DELETE'])
def delete_entry(resource_id, entry_id):
    resourcemgr.delete_entry(resource_id, entry_id)
    return flask_jsonify({'status': 'removed'})
