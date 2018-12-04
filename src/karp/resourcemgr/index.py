
class IndexInterface:

    def create_index(self, resource_id, config):
        return []

    def publish_index(self, alias_name, index_name):
        return

    def add_entries(self, resource_id, created_db_entries):
        return


class IndexModule(IndexInterface):

    def __init__(self):
        self.impl = IndexInterface()

    def init(self, impl):
        self.impl = impl

    def create_index(self, resource_id, config):
        return self.impl.create_index(resource_id, config)

    def publish_index(self, alias_name, index_name):
        return self.impl.publish_index(alias_name, index_name)

    def add_entries(self, resource_id, created_db_entries):
        self.impl.add_entries(resource_id, created_db_entries)


index_mgr = IndexModule()
