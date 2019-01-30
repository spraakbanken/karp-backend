
class IndexInterface:

    def create_index(self, resource_id, config):
        raise NotImplementedError()

    def publish_index(self, alias_name, index_name):
        raise NotImplementedError()

    def add_entries(self, resource_id, entries):
        raise NotImplementedError()

    def delete_entry(self, resource_id, entry_id):
        raise NotImplementedError()

    def create_empty_object(self):
        raise NotImplementedError()

    def assign_field(self, _index_entry, field_name, part):
        raise NotImplementedError()

    def create_empty_list(self):
        raise NotImplementedError()

    def add_to_list_field(self, elems, elem):
        raise NotImplementedError()


class IndexModule:

    def __init__(self):
        self.impl = IndexInterface()

    def init(self, impl):
        self.impl = impl
