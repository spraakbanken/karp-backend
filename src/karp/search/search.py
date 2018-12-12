class SearchInterface:

    def get_query(self, resources):
        return None

    def search(self, resources, query=None):
        return []


class KarpSearch(SearchInterface):

    def __init__(self):
        self.impl = SearchInterface()

    def init(self, impl):
        self.impl = impl

    def get_query(self, resources):
        return self.impl.get_query(resources)

    def search(self, resources, query=None):
        return self.impl.search(resources, query=query)
