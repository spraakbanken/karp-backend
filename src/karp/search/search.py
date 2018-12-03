from elasticsearch_dsl import Search, Q


class KarpSearch:

    def __init__(self):
        self.impl = SearchInterface()

    def init(self, impl):
        self.impl = impl

    def get_query(self, *args, **kwargs):
        return self.impl.get_query(*args, **kwargs)

    def search(self, *args, **kwargs):
        return self.impl.search(*args, **kwargs)

    def create_index(self, *args, **kwargs):
        return self.impl.create_index(*args, **kwargs)

    def publish_index(self, *args, **kwargs):
        return self.impl.publish_index(*args, **kwargs)

    def add_entries(self, *args, **kwargs):
        self.impl.add_entries(*args, **kwargs)


class SearchInterface:

    def get_query(self, resources):
        return None

    def search(self, resources, query=None):
        return []

    def create_index(self, resource_id, config):
        return []

    def publish_index(self, alias_name, index_name):
        return

    def add_entries(self, resource_id, created_db_entries):
        return
