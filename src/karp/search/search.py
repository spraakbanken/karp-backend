import distutils

from typing import Optional, Callable, TypeVar, List, Dict

from karp import util

from . import errors
from . import query_parser as parser


T = TypeVar('T', bool, int, str, List[str])


def arg_get(args,
            arg_name: str,
            convert: Optional[Callable[[str], T]] = None,
            default: Optional[T] = None) -> T:
    arg = args.get(arg_name, None)
    if arg is None:
        return default
    if convert is None:
        return arg
    return convert(arg)


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
        'split_results': {'default': False, 'convert': distutils.util.strtobool},
        'lexicon_stats': {'default': True, 'convert': distutils.util.strtobool},
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


class Query:
    from_ = 0
    size = 25
    split_results = False
    lexicon_stats = True
    include_fields = None
    exclude_fields = None
    fields = []
    format = None
    format_query = None
    q = None
    resources = []
    sort = ""

    def __init__(self):
        pass

    def parse_arguments(self, args, resource_str: str):
        if resource_str is None:
            raise errors.IncompleteQuery('No resources are defined.')
        self.resources = resource_str.split(',')
        self.from_ = arg_get(args, 'from', int, 0)
        self.size = arg_get(args, 'size', int, 25)
        self.split_results = arg_get(args, 'split_results', distutils.util.strtobool, False)
        self.lexicon_stats = arg_get(args, 'lexicon_stats', distutils.util.strtobool, True)
        self.include_fields = arg_get(args, 'include_fields', util.convert.str2list(','))
        self.exclude_fields = arg_get(args, 'exclude_fields', util.convert.str2list(','))
        self.format = arg_get(args, 'format')
        self.format_query = arg_get(args, 'format_query')
        self.q = arg_get(args, 'q')
        self.sort = arg_get(args, 'sort')

        _parser = parser.QueryParser()
        self.ast = _parser.parse(self.q)

    def __repr__(self) -> str:
        return """
            {}(
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
            )""".format(self._self_name(),
                        self.q,
                        self.resources,
                        self.include_fields,
                        self.exclude_fields,
                        self.fields if self.fields else [],
                        self.sort,
                        self.from_, self.size,
                        self.split_results, self.lexicon_stats,
                        self.format,
                        self.format_query)

    def _self_name(self) -> str:
        return 'Query'


class SearchInterface:

    def build_query(self, args, resource_str: str) -> Query:
        query = Query()
        query.parse_arguments(args, resource_str)
        return query

    def search_with_query(self, query: Query):
        return []

    def get_query(self, resources):
        return None

    def search(self, resources, query=None):
        return []


class KarpSearch(SearchInterface):

    def __init__(self):
        self.impl = SearchInterface()

    def init(self, impl: SearchInterface):
        self.impl = impl

    def build_query(self, args, resource_str: str) -> Query:
        return self.impl.build_query(args, resource_str)

    def search_with_query(self, query: Query):
        return self.impl.search_with_query(query)

    def get_query(self, resources):
        return self.impl.get_query(resources)

    def search(self, resources, query=None):
        return self.impl.search(resources, query=query)
