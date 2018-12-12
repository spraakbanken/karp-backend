
class IndexInterface:

    def create_index(self, resource_id, config):
        return 'dummy'

    def publish_index(self, alias_name, index_name):
        return

    def add_entries(self, resource_id, entries):
        return

    def delete_entry(self, resource_id, entry_id):
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

    def add_entries(self, resource_id, entries):
        self.impl.add_entries(resource_id, entries)

    def delete_entry(self, resource_id, entry_id):
        self.impl.delete_entry(resource_id, entry_id)


index_mgr = IndexModule()