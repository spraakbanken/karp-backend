import json

from flask import Blueprint                     # pyre-ignore
from flask import jsonify as flask_jsonify       # pyre-ignore
from flask import request  # pyre-ignore

from karp.resourcemgr import entrywrite
from karp.errors import KarpError
import karp.auth.auth as auth

edit_api = Blueprint('edit_api', __name__)


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
    version = data.get('version')
    entry = data.get('entry')
    message = data.get('message')
    if not (version and entry and message):
        raise KarpError('Missing field')
    entrywrite.update_entry(resource_id, entry_id, version, entry, user.identifier, message=message)
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
