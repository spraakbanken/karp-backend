"""
Perform health checks on the server.

Used to perform readiness and liveness probes on the server.
"""

from typing import List
from typing import Optional
from typing import Dict
from typing import TypeVar
from typing import Callable
# from typing import ImmutableMapping

from distutils.util import strtobool
import json

from flask import Blueprint, jsonify, request    # pyre-ignore

from karp.resourcemgr import Resource
from karp.resourcemgr import get_resource

from karp import search

from karp import util


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
    sort: str = ""
    resource_params: Dict[str, Dict] = {}

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
                resource_params={}
            """.format(self.q,
                       self.resources if self.resources else [],
                       self.include_fields,
                       self.exclude_fields,
                       self.fields if self.fields else [],
                       self.sort,
                       self.from_, self.size,
                       self.split_results, self.lexicon_stats,
                       self.format,
                       self.format_query,
                       json.dumps(self.resource_params))

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


def read_general_arguments() -> QueryParameters:
    params = QueryParameters()
    if request.args.get('from'):
        params.from_ = int(request.args.get('from'))
    if request.args.get('size'):
        params.size = int(request.args.get('size'))
    if request.args.get('split_results'):
        params.split_results = strtobool(request.args.get('split_results'))
    if request.args.get('lexicon_stats'):
        params.lexicon_stats = strtobool(request.args.get('lexicon_stats'))
    if request.args.get('format'):
        params.format = request.args.get('format')
    if request.args.get('q'):
        params.q = request.args.get('q')
    if request.args.get('include_fields'):
        params.include_fields = request.args.get('include_fields').split(',')
    if request.args.get('exclude_fields'):
        params.exclude_fields = request.args.get('exclude_fields').split(',')
    return params


T = TypeVar('T', bool, int, str, List[str])


def arg_get(arg_name: str,
            convert: Optional[Callable[[str], T]] = None,
            default: Optional[T] = None) -> T:
    arg = request.args.get(arg_name)
    if not arg:
        return default
    if not convert:
        return arg
    return convert(arg)


def read_resource_arguments(params: Dict,
                            resource: Resource) -> Dict:
    format_query = arg_get('format_query')
    resource_params = {}
    if format_query:
        if resource.has_format_query(format_query):
            resource_params['format_query'] = format_query
        else:
            # TODO What do if the user called with a unsupported format_query
            raise RuntimeError

    if not params.get('sort'):
        resource_params['sort'] = resource.default_sort()

    # Populate list over all fields to search for
    if params.get('include_fields'):
        fields = params['include_fields']
    else:
        fields = resource.get_fields()

    # Remove excluded fields from the intial list
    for field in params.get('exclude_fields', []):
        fields.remove(field)

    resource_params['fields'] = fields

    if not params.get('resource_params'):
        params['resource_params'] = {}
    params['resource_params'][resource.id()] = resource_params

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
    return jsonify(response)


@query_api.route('/<resource_id>/<entry_id>/get_indexed', methods=['GET'])
def get_indexed_entry(resource_id, entry_id):
    # TODO a temporary soulution until search is done
    from elasticsearch_dsl import Q, Search
    s = Search(using=search.search.impl.es, index=resource_id)
    s = s.query(Q('term', _id=entry_id))
    response = s.execute()
    result = {
        'entry': response[0].to_dict(),
        'id': response[0].meta.id,
        'version': -1
    }




def get_fields(name: str, include_fields: List[str], exclude_fields: List[str]) -> List[str]:
    return []


def parse_arguments(args: Dict[str, str], resource_str: str = None) -> Dict:
    params = {}
    s2l = util.convert.str2list(',')
    if resource_str:
        params['resources'] = arg_get('resources', s2l)
    else:
        params['resources'] = s2l(resource_str)
    available_fields = {
        'from': {'default': 0, 'convert': int},
        'size': {'default': 25, 'convert': int},
        'split_results': {'default': False, 'convert': strtobool},
        'lexicon_stats': {'default': True, 'convert': strtobool},
        'include_fields': {'convert': s2l},
        'exclude_fields': {'convert': s2l},
        'format': {},
        'format_query': {},
        'q': {},
        'sort': {}
    }

    for field, m in available_fields.items():
        params[field] = arg_get(field, m.get('convert'), m.get('default'))

    return params



    return jsonify(result), 200

    # resources = resources.split(',')
    # result = {}
    # query_params = read_general_arguments()
    # query_params.resources = resources
    # for resource_id in resources:
    #     resource_result = {}
    #     resource = get_resource(resource_id)
    #     query_params = read_resource_arguments(query_params, resource)
    #     print("/query got resource: {resource}".format(resource=resource_id))
    #     print(resource)
    #     print(query_params)
    #     if not user_is_authorized(resource=resource,
    #                               fields=query_params.fields):
    #         return jsonify({'status': 'forbidden'}), 403
    #
    #     hits: List[str] = []
    #
    #     for i in range(query_params.from_, query_params.from_ + query_params.size):
    #         hits.append("{}[{}]".format(resource_id, str(i)))
    #
    #     resource_result['hits'] = hits
    #
    #     # es_result = search.search(resource_id, resource.version, simple_query="Kommun")
    #     # resource_result['es'] = es_result
    #     result[resource_id] = resource_result
    #
    # result['query_params'] = repr(query_params)
    #
    # print(result)
    # return jsonify(result), 200
