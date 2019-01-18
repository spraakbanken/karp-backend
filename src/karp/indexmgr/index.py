
class IndexInterface:

    def create_index(self, resource_id, config):
        return 'dummy'

    def publish_index(self, alias_name, index_name):
        return

    def add_entries(self, resource_id, entries):
        return

    def delete_entry(self, resource_id, entry_id):
        return

    def create_empty_object(self):
        return {}

    def assign_field(self, _index_entry, field_name, part):
        return

    def create_empty_list(self):
        return []

    def add_to_list_field(self, elems, elem):
        return


class IndexModule:

    def __init__(self):
        self.impl = IndexInterface()

    def init(self, impl):
        self.impl = impl
