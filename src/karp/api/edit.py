from flask import Blueprint                     # pyre-ignore
from flask import jsonify as flask_jsonify       # pyre-ignore
from flask import request  # pyre-ignore
import json

import karp.resourcemgr.entrymgr as entrymgr


edit_api = Blueprint('edit_api', __name__)


@edit_api.route('/<resource_id>/<entry_id>')
def get_entry_for_editing(resource_id, entry_id):
    db_entry = entrymgr.get_entry(resource_id, entry_id)
    result = {
        'id': entry_id,
        'version': -1,  # TODO: version are only available in history right now
        'entry': json.loads(db_entry.body)
    }
    return flask_jsonify(result)


@edit_api.route('/<resource_id>/add', methods=['POST'])
def add_entry(resource_id):
    data = request.get_json()
    new_id = entrymgr.add_entry(resource_id, data['entry'], message=data['message'])
    return flask_jsonify({'status': 'added', 'newID': new_id}), 201


@edit_api.route('/<resource_id>/_all')
def get_all_entries(resource_id):
    """
    TODO replace using this with /query call without a query
    """
    entries = entrymgr.get_entries(resource_id)
    return flask_jsonify(entries)


@edit_api.route('/<resource_id>/<entry_id>/update', methods=['POST'])
def update_entry(resource_id, entry_id):
    data = request.get_json()
    version = data['version']  # TODO: use this
    entrymgr.update_entry(resource_id, entry_id, data['entry'], message=data['message'])
    return flask_jsonify({'status': 'updated'})


@edit_api.route('/<resource_id>/<entry_id>/delete', methods=['DELETE'])
def delete_entry(resource_id, entry_id):
    entrymgr.delete_entry(resource_id, entry_id)
    return flask_jsonify({'status': 'removed'})


@edit_api.route('/<resource_id>/preview', methods=['POST'])
def preview_entry(resource_id):
    data = request.get_json()
    preview = entrymgr.preview_entry(resource_id, data)
    return flask_jsonify(preview)
