import json
from flask import Blueprint                     # pyre-ignore
from flask import jsonify as flask_jsonify       # pyre-ignore
from flask import request  # pyre-ignore

import karp.resourcemgr as database


edit_api = Blueprint('crud_api', __name__)

"""

    <resource>/delete/<id> DELETE
    <resource>/add POST alt. <resource>/add_without_message POST
        data: { object }
    <resource>/add_with_message POST alt. <resource>/add POST
        data: { 'doc': { object }, 'message': "" }
    <resource>/update/<id> POST
        data: { 'doc': ..., 'version': "", 'message': "" }

"""

@edit_api.route("/entry", methods=['POST'])
def add_entry():
    """
    Example add: `curl -XPOST http://localhost:5000/entry?resource=places
                 -d '{"name": "Göteborg", "population": 3, "area": 30000}' -H "Content-Type: application/json"`
    """
    resource = request.args.get('resource')
    data = request.get_json()
    database.add_entry(resource, data)
    return flask_jsonify({'status': 'added'}), 201


@edit_api.route("/<resource_id>/delete/<entry_id>", methods=['DELETE'])
def delete_entry(resource_id, entry_id):
    database.delete_entry(resource_id, entry_id)
    return flask_jsonify({'status': 'removed'})
