"""
Perform health checks on the server.

Used to perform readiness and liveness probes on the server.
"""
import logging
from typing import List


from flask import Blueprint, jsonify as flask_jsonify, request    # pyre-ignore

from karp.resourcemgr import Resource

from karp import search
import karp.auth.auth as auth
from karp import errors


_logger = logging.getLogger('karp')


query_api = Blueprint('query_api', __name__)


@query_api.route('/<resource_id>/<entry_ids>')
@auth.auth.authorization('READ')
def get_entries_by_id(resource_id: str, entry_ids: str):
    response = search.search.search_ids(request.args, resource_id, entry_ids)
    return flask_jsonify(response)


@query_api.route('/<resources>/query', methods=['GET'])
@query_api.route('/query/<resources>', methods=['GET'])
@auth.auth.authorization('READ')
def query(resources: str):
    print('query_w_resources called with resources={}'.format(resources))
    try:
        query = search.search.build_query(request.args, resources)
        print('query={}'.format(query))
        response = search.search.search_with_query(query)
    except errors.KarpError as e:
        _logger.exception("Error occured when calling 'query' with resources='{}' and q='{}'".format(resources, request.args.get('q')))
        raise
    return flask_jsonify(response), 200


@query_api.route('/<resource_id>/<entry_id>/get_indexed', methods=['GET'])
@auth.auth.authorization('READ')
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
    return flask_jsonify(result), 200
