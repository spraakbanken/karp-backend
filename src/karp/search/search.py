class SearchQuery:
    pass


class SearchInterface:

    def get_query(self, resources):
        return None

    def search(self, resources, query=None):
        return []

    def build_query(self, query_params) -> SearchQuery:
        raise NotImplementedError


class KarpSearch(SearchInterface):

    def __init__(self):
        self.impl = SearchInterface()

    def init(self, impl: SearchInterface):
        self.impl = impl

    def get_query(self, resources):
        return self.impl.get_query(resources)

    def build_query(self, query_params) -> SearchQuery:
        return self.impl.build_query(query_params)

    def search(self, resources, query=None):
        return self.impl.search(resources, query=query)
