import distutils

from typing import Optional, Callable, TypeVar, List

from . import errors


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


class Query:
    resource = []

    def __init__(self):
        pass

    def parse_arguments(self, args, resource_str: str):
        if resource_str is None:
            raise errors.IncompleteQuery('No resources are defined.')
        self.resources = resource_str.split(',')
        self.split_results = arg_get(args, 'split_results', distutils.util.strtobool, False)

    def __repr__(self) -> str:
        return '{} resources={} split_results={}'.format(self._self_name(),
                                                         self.resources,
                                                         self.split_results)

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
