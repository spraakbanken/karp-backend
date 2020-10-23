"""
Perform health checks on the server.

Used to perform readiness and liveness probes on the server.
"""
import logging

from flask import Blueprint, jsonify as flask_jsonify, request  # pyre-ignore

from karp import resourcemgr

from karp import search
import karp.auth.auth as auth
from karp import errors


_logger = logging.getLogger("karp")


query_api = Blueprint("query_api", __name__)


@query_api.route("/entries/<resource_id>/<entry_ids>")
@auth.auth.authorization("READ")
def get_entries_by_id(resource_id: str, entry_ids: str):
    response = search.search_ids(request.args, resource_id, entry_ids)
    return flask_jsonify(response)


# @query_api.route("/<resources>/query", methods=["GET"])
@query_api.route("/query/<resources>", methods=["GET"])
@auth.auth.authorization("READ")
def query(resources: str):
    print("Called 'query' called with resources={}".format(resources))
    resource_list = resources.split(",")
    resourcemgr.check_resource_published(resource_list)
    try:
        q = search.build_query(request.args, resources)
        print("query::q={q}".format(q=q))
        response = search.search_with_query(q)
    except errors.KarpError as e:
        _logger.exception(
            "Error occured when calling 'query' with resources='{}' and q='{}'. e.msg='{}".format(
                resources, request.args.get("q"), e.message
            )
        )
        raise
    return flask_jsonify(response), 200


# @query_api.route("/<resources>/query_split", methods=["GET"])
@query_api.route("/query_split/<resources>", methods=["GET"])
@auth.auth.authorization("READ")
def query_split(resources: str):
    print("query_split called with resources={}".format(resources))
    resource_list = resources.split(",")
    resourcemgr.check_resource_published(resource_list)
    try:
        query = search.build_query(request.args, resources)
        query.split_results = True
        print("query={}".format(query))
        response = search.search_with_query(query)
    except errors.KarpError as e:
        _logger.exception(
            "Error occured when calling 'query' with resources='{}' and q='{}'. msg='{}'".format(
                resources, request.args.get("q"), e.message
            )
        )
        raise
    return flask_jsonify(response), 200
