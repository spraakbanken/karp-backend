"""
Perform health checks on the server.

Used to perform readiness and liveness probes on the server.
"""

from flask import Blueprint, jsonify
import karp.database as database

karp_health_api = Blueprint('karp_health_api', __name__)


@karp_health_api.route('/healthz', methods=['GET'])
def perform_health_check():
    status, msg = database.health_database_status()
    if status:
        return jsonify({'status': 'ok'}), 200
    else:
        return jsonify({'status': msg}), 500
