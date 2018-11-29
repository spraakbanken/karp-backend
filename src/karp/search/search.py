from elasticsearch_dsl import Search, Q


class KarpSearch:

    def __init__(self):
        self.impl = SearchInterface()

    def init(self, impl):
        self.impl = impl

    def search(self, *args, **kwargs):
        return self.impl.search(*args, **kwargs)

    def create_index(self, *args, **kwargs):
        return self.impl.create_index(*args, **kwargs)

    def add_entries(self, *args, **kwargs):
        self.impl.add_entries(*args, **kwargs)


class SearchInterface:

    def search(self, resource_id, version, simple_query=None, extended_query=None):
        return []

    def create_index(self, resource_id, version, config):
        return []

    def add_entries(self, resource_id, version, created_db_entries):
        return
