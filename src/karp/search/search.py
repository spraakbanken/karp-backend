
from typing import Optional, Callable, TypeVar, List, Dict

from karp.util import convert as util_convert

from karp import query_dsl

from . import errors


T = TypeVar('T', bool, int, str, List[str])


def arg_get(args: Dict,
            arg_name: str,
            convert: Optional[Callable[[str], T]] = None,
            default: Optional[T] = None) -> T:
    arg = args.get(arg_name, None)
    if arg is None:
        return default
    if convert is None:
        return arg
    return convert(arg)


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
        self.split_results = arg_get(args, 'split_results', util_convert.str2bool, False)
        self.lexicon_stats = arg_get(args, 'lexicon_stats', util_convert.str2bool, True)
        self.include_fields = arg_get(args, 'include_fields', util_convert.str2list(','))
        self.exclude_fields = arg_get(args, 'exclude_fields', util_convert.str2list(','))
        self.fields = []
        self.format = arg_get(args, 'format')
        self.format_query = arg_get(args, 'format_query')
        self.q = arg_get(args, 'q')
        self.sort = arg_get(args, 'sort')

        self.ast = query_dsl.parse(self.q)

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
            )""".format(self._self_name(),
                        self.q,
                        self.resources,
                        self.include_fields,
                        self.exclude_fields,
                        self.fields,
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
        raise NotImplementedError()


class KarpSearch(SearchInterface):

    def __init__(self):
        self.impl = SearchInterface()

    def init(self, impl: SearchInterface):
        self.impl = impl

    def build_query(self, args, resource_str: str) -> Query:
        return self.impl.build_query(args, resource_str)

    def search_with_query(self, query: Query):
        return self.impl.search_with_query(query)
