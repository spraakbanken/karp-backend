from flask import Blueprint, jsonify    # pyre-ignore

from karp import search
import karp.auth.auth as auth
import karp.resourcemgr.entryread as entryread
import karp.resourcemgr as resourcemgr

history_api = Blueprint('history_api', __name__)


@history_api.route('/<resource_id>/<entry_id>/diff/<version1>/<version2>', methods=['GET'])
@auth.auth.authorization('READ')
def get_diff(resource_id, entry_id, version1, version2):
    diff = entryread.diff(resourcemgr.get_resource(resource_id), entry_id, version1, version2)
    return jsonify({'diff': diff})
