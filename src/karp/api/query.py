"""
Perform health checks on the server.

Used to perform readiness and liveness probes on the server.
"""

from typing import List


from flask import Blueprint, jsonify, request    # pyre-ignore

from karp.resourcemgr import Resource

from karp import search


query_api = Blueprint('query_api', __name__)


def user_is_authorized(resource: Resource, fields: List[str], mode="read") -> bool:
    if resource.is_protected(mode=mode, fields=fields):
        return False
    else:
        return True


@query_api.route('/<resources>/query', methods=['GET'])
@query_api.route('/query/<resources>', methods=['GET'])
def query_w_resources(resources: str):
    print('query_w_resources called with resources={}'.format(resources))
    query = search.search.build_query(request.args, resources)
    print('query={}'.format(query))
    response = search.search.search_with_query(query)
    print('response={}'.format(response))
    return jsonify(response), 200


@query_api.route('/<resource_id>/<entry_id>/get_indexed', methods=['GET'])
def get_indexed_entry(resource_id, entry_id):
    # TODO a temporary soulution until search is done
    from elasticsearch_dsl import Q, Search  # pyre-ignore
    s = Search(using=search.search.impl.es, index=resource_id)
    s = s.query(Q('term', _id=entry_id))
    response = s.execute()
    result = {
        'entry': response[0].to_dict(),
        'id': response[0].meta.id,
        'version': -1
    }
    return jsonify(result), 200
