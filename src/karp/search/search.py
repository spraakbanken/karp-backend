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


class KarpSearch(SearchInterface):

    def __init__(self):
        self.impl = SearchInterface()

    def init(self, impl):
        self.impl = impl

    def get_query(self, resources):
        return self.impl.get_query(resources)

    def search(self, resources, query=None):
        return self.impl.search(resources, query=query)

    def create_index(self, resource_id, config):
        return self.impl.create_index(resource_id, config)

    def publish_index(self, alias_name, index_name):
        return self.impl.publish_index(alias_name, index_name)

    def add_entries(self, resource_id, created_db_entries):
        self.impl.add_entries(resource_id, created_db_entries)
