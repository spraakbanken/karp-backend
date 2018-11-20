"""
Perform health checks on the server.

Used to perform readiness and liveness probes on the server.
"""

from flask import Blueprint, jsonify    # pyre-ignore

query_api = Blueprint('query_api', __name__)


@query_api.route('/query', methods=['GET'])
def perform_query():
    return jsonify({'status': 'ok'}), 200
