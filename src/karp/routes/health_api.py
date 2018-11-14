"""
Perform health checks on the server.

Used to perform readiness and liveness probes on the server.
"""

from flask import Blueprint, jsonify    # pyre-ignore
import karp.database as database

health_api = Blueprint('health_api', __name__)


@health_api.route('/healthz', methods=['GET'])
def perform_health_check():
    status, msg = database.check_database_status()
    if status:
        return jsonify({'status': 'ok'}), 200
    else:
        return jsonify({'status': msg}), 500
