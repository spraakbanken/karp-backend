from flask import Blueprint                     # pyre-ignore
from flask import jsonify as flask_jsonify       # pyre-ignore
from flask import request  # pyre-ignore

import karp.resourcemgr.entrymgr as entrymgr


edit_api = Blueprint('edit_api', __name__)


@edit_api.route('/<resource_id>/add', methods=['POST'])
def add_entry(resource_id):
    """
    Example add: `curl -XPOST http://localhost:5000/entry?resource=places
                 -d '{"name": "Göteborg", "population": 3, "area": 30000}' -H "Content-Type: application/json"`
    """
    data = request.get_json()
    new_id = entrymgr.add_entry(resource_id, data)
    return flask_jsonify({'status': 'added', 'newID': new_id}), 201


@edit_api.route('/<resource_id>/add_with_message', methods=['POST'])
def add_entry_with_msg(resource_id):
    data = request.get_json()
    new_id = entrymgr.add_entry(resource_id, data['doc'], message=data['message'])
    return flask_jsonify({'status': 'added', 'newID': new_id}), 201


@edit_api.route('/<resource_id>/_all')
def get_all_entries(resource_id):
    """
    TODO replace using this with /query call without a query
    """
    entries = entrymgr.get_entries(resource_id)
    return flask_jsonify(entries)


@edit_api.route('/<resource_id>/_all_indexed')
def get_all_indexed_entries(resource_id):
    """
    TODO replace using this with /query call without a query
    """
    entries = entrymgr.get_entries_indexed(resource_id)
    return flask_jsonify(entries)


@edit_api.route('/<resource_id>/update/<entry_id>', methods=['POST'])
def update_entry(resource_id, entry_id):
    data = request.get_json()
    entrymgr.update_entry(resource_id, entry_id, data['doc'], message=data['message'])
    return flask_jsonify({'status': 'updated'})


@edit_api.route('/<resource_id>/delete/<entry_id>', methods=['DELETE'])
def delete_entry(resource_id, entry_id):
    entrymgr.delete_entry(resource_id, entry_id)
    return flask_jsonify({'status': 'removed'})


@edit_api.route('/<resource_id>/preview', methods=['POST'])
def preview_entry(resource_id):
    data = request.get_json()
    preview = entrymgr.preview_entry(resource_id, data)
    return flask_jsonify(preview)
