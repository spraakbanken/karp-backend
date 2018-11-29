"""
Perform health checks on the server.

Used to perform readiness and liveness probes on the server.
"""

from typing import List, Optional, TypeVar
from distutils.util import strtobool

from flask import Blueprint, jsonify, request    # pyre-ignore

from karp.resourcemgr import Resource
from karp.resourcemgr import get_resource


query_api = Blueprint('query_api', __name__)


class QueryParameters(object):
    from_: int = 0
    size: int = 25
    split_results: bool = False
    lexicon_stats: bool = True
    include_fields: Optional[List[str]] = None
    exclude_fields: Optional[List[str]] = None
    fields: List[str] = []
    format: Optional[str] = None
    format_query: Optional[str] = None
    q: Optional[str] = None
    resources: List[str] = []
    sort: Optional[str] = None

    def __repr__(self) -> str:
        return """
            <QueryParameters(
                q={}
                resources={}
                include_fields={}
                exclude_fields={}
                fields={}
                sort={}
                from={}, size={},
                split_results={}, lexicon_stats={},
                format={}
                format_query={}
            """.format(self.q,
                       self.resources if self.resources else [],
                       self.include_fields,
                       self.exclude_fields,
                       self.fields if self.fields else [],
                       self.sort,
                       self.from_, self.size,
                       self.split_results, self.lexicon_stats,
                       self.format,
                       self.format_query)

    # def get_from(self) -> int:
    #     return self.from_
    #
    # def get_size(self) -> int:
    #     return self.size
    #
    # def get_split_results(self) -> bool:
    #     return self.split_results
    #
    # def get_lexicon_stats(self) -> bool:
    #     return self.lexicon_stats
    #
    # def get_include_fields(self) -> Optional[List[str]]:
    #     return self.include_fields
    #
    # def get_exclude_fields(self) -> Optional[List[str]]:
    #     return self.exclude_fields
    #
    # def get_format(self) -> Optional[str]:
    #     return self.format
    #
    # def get_format_query(self) -> Optional[str]:
    #     return self.format_query
    #
    # def get_q(self) -> Optional[str]:
    #     return self.q
    #
    # def get_resources(self) -> List[str]:
    #     return self.resources
    #
    # def get_sort(self) -> Optional[str]:
    #     return self.sort


class DefaultQueryParameters(QueryParameters):
    params = {
        'from': 0,
        'size': 25,
        'split_results': False,
        'lexicon_stats': True,
        'include_fields': None,
        'exclude_fields': None,
        'format': None,
        'format_query': None,
        'q': None,
        'resources': None,
        'sort': None
    }
    pass


class ResourceQueryParameters(QueryParameters):
    def __init__(self, resource: Resource) -> None:
        super().__init__()
        self.sort = resource.default_sort()


def read_arguments(resource: Resource) -> QueryParameters:
    params = ResourceQueryParameters(resource)
    if request.args.get('from'):
        params.from_ = int(request.args.get('from'))
    if request.args.get('size'):
        params.size = int(request.args.get('size'))
    if request.args.get('split_results'):
        params.split_results = strtobool(request.args.get('split_results'))
    if request.args.get('lexicon_stats'):
        params.lexicon_stats = strtobool(request.args.get('lexicon_stats'))
    if request.args.get('include_fields'):
        params.include_fields = request.args.get('include_fields').split(',')
    if request.args.get('exclude_fields'):
        params.exclude_fields = request.args.get('exclude_fields').split(',')
    if request.args.get('format'):
        params.format = request.args.get('format')
    if request.args.get('format_query'):
        params.format_query = request.args.get('format_query')
    if request.args.get('sort'):
        params.sort = request.args.get('sort')

    # Populate list over all fields to search for
    if params.include_fields:
        fields = params.include_fields
    else:
        fields = resource.get_fields()

    # Remove excluded fields from the intial list
    if params.exclude_fields:
        for field in params.exclude_fields:
            fields.remove(field)

    params.fields = fields
    return params


# def do_query(resources: List[Resource]):
#
#
#
# @query_api.route('/query', methods=['GET'])
# def query():
#     log_arguments()
#     resources = request.args.get('resources').split(',')
#     query_params = read_arguments(resources)
#
#     for resource_id in resources:
#         resource = resource_store.get_resource(resource_id)
#
#         if not user_is_permitted(resource_id):
#             return jsonify({'status': 'forbidden'}), 403
#         print("/query got resource: {resource}".format(resource=resource_id))
#     return jsonify({'status': 'ok'}), 200


def user_is_authorized(resource: Resource, fields: List[str]) -> bool:
    if resource.is_protected():
        return False
    else:
        return True


@query_api.route('/<resources>/query', methods=['GET'])
@query_api.route('/query/<resources>', methods=['GET'])
def query_w_resources(resources: str):
    resources = resources.split(',')
    result = {}
    for resource_id in resources:
        resource = get_resource(resource_id)
        query_params = read_arguments(resource)
        print("/query got resource: {resource}".format(resource=resource_id))
        print(resource)
        print(query_params)
        if not user_is_authorized(resource=resource,
                                  fields=query_params.fields):
            return jsonify({'status': 'forbidden'}), 403
        hits: List[str] = []

        for i in range(query_params.from_, query_params.from_ + query_params.size):
            hits.append("{}[{}]".format(resource_id, str(i)))

        result['hits'] = hits

    print(result)

    return jsonify(hits=result), 200
