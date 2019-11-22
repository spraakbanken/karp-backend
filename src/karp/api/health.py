"""
Perform health checks on the server.

Used to perform readiness and liveness probes on the server.
"""

from flask import Blueprint, jsonify  # pyre-ignore

from karp.system_monitor import check_database_status

health_api = Blueprint("health_api", __name__)


@health_api.route("/healthz", methods=["GET"])
def perform_health_check():
    status, msg = check_database_status()
    if status:
        return jsonify({"database": "ok"}), 200
    else:
        return jsonify({"database": msg}), 500
