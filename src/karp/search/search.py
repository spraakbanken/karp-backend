from . import errors


class Query:
    resource = []

    def __init__(self):
        pass

    def parse_arguments(self, args, resource_str: str):
        if resource_str is None:
            raise errors.IncompleteQuery('No resources are defined.')
        self.resources = resource_str.split(',')


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
