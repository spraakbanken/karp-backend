from flask import Blueprint, jsonify    # pyre-ignore

from karp import search
import karp.auth.auth as auth

stats_api = Blueprint('stats_api', __name__)


@stats_api.route('/stats/<resource_id>/<field>', methods=['GET'])
@auth.auth.authorization('READ')
def get_field_values(resource_id, field):
    return jsonify(search.search.statistics(resource_id, field))
