from flask import Blueprint, jsonify, request    # pyre-ignore

import karp.auth.auth as auth
import karp.resourcemgr.entryread as entryread
import karp.resourcemgr as resourcemgr

history_api = Blueprint('history_api', __name__)


@history_api.route('/<resource_id>/<entry_id>/diff', methods=['GET', 'POST'])
@auth.auth.authorization('ADMIN')
def get_diff(resource_id, entry_id):
    """
    Get diff between two entries
    1. Needed for this call to work, at least from_version/from_date OR to_version/to_date
    2. If a to_* is given, but no from_*, diff from first version
    3. If a from_* is given, but no to_*, diff to latest version
    4. *_version trumps *_date
    5. If an entry is sent as JSON-data is sent in, this will be used instead of first/last version as described above
    6. If both from_* and to_* are given, entry data will not be used
    """
    from_version = request.args.get('from_version')
    to_version = request.args.get('to_version')
    # from_date = request.args.get('from_version')
    # to_date = request.args.get('to_version')
    # entry = request.get_json()
    diff = entryread.diff(resourcemgr.get_resource(resource_id), entry_id, from_version, to_version)
    return jsonify({'diff': diff})


@history_api.route('/<resource_id>/<user_id>/history', methods=['GET'])
@auth.auth.authorization('ADMIN')
def get_user_history(resource_id, user_id):
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    pass


@history_api.route('/<resource_id>/<entry_id>/history', methods=['GET'])
@auth.auth.authorization('ADMIN')
def get_entry_history(resource_id, entry_id):
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    from_version = request.args.get('from_version')
    to_version = request.args.get('to_version')
    pass
