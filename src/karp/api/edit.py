import json

from flask import Blueprint                     # pyre-ignore
from flask import jsonify as flask_jsonify       # pyre-ignore
from flask import request  # pyre-ignore

from karp.resourcemgr import entrywrite
from karp.resourcemgr import entryread
import karp.auth.auth as auth

edit_api = Blueprint('edit_api', __name__)


@edit_api.route('/<resource_id>/<entry_id>')
@auth.auth.authorization('READ')
def get_entry_for_editing(resource_id, entry_id):
    db_entry = entryread.get_entry(resource_id, entry_id)
    result = {
        'id': entry_id,
        'version': -1,  # TODO: version are only available in history right now
        'entry': json.loads(db_entry.body)
    }
    return flask_jsonify(result)


@edit_api.route('/<resource_id>/add', methods=['POST'])
@auth.auth.authorization('WRITE', add_user=True)
def add_entry(user, resource_id):
    data = request.get_json()
    new_id = entrywrite.add_entry(resource_id, data['entry'], user.identifier, message=data.get('message', ''))
    return flask_jsonify({'status': 'added', 'newID': new_id}), 201


@edit_api.route('/<resource_id>/<entry_id>/update', methods=['POST'])
@auth.auth.authorization('WRITE', add_user=True)
def update_entry(user, resource_id, entry_id):
    data = request.get_json()
    entrywrite.update_entry(resource_id, entry_id, data['entry'], user.identifier, message=data['message'])
    return flask_jsonify({'status': 'updated'})


@edit_api.route('/<resource_id>/<entry_id>/delete', methods=['DELETE'])
@auth.auth.authorization('WRITE', add_user=True)
def delete_entry(user, resource_id, entry_id):
    entrywrite.delete_entry(resource_id, entry_id, user.identifier)
    return flask_jsonify({'status': 'removed'})


@edit_api.route('/<resource_id>/preview', methods=['POST'])
@auth.auth.authorization('READ')
def preview_entry(resource_id):
    data = request.get_json()
    preview = entrywrite.preview_entry(resource_id, data)
    return flask_jsonify(preview)
