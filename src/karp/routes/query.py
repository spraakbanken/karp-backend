"""
Perform health checks on the server.

Used to perform readiness and liveness probes on the server.
"""

from flask import Blueprint, jsonify    # pyre-ignore

query_api = Blueprint('query_api', __name__)


def user_is_permitted(resource_id: str) -> bool:
    if resource_id == "protected":
        return False
    else:
        return True


@query_api.route('/<resources>/query', methods=['GET'])
@query_api.route('/query/<resources>', methods=['GET'])
def query(resources):
    resources = resources.split(',')
    for resource in resources:
        if not user_is_permitted(resource):
            return jsonify({'status': 'forbidden'}), 403
        print("/query got resource: {resource}".format(resource=resource))
    return jsonify({'status': 'ok'}), 200
