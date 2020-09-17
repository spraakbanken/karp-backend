from typing import Dict, List, Tuple
from karp.resourcemgr.entrymetadata import EntryMetadata


class IndexInterface:
    def create_index(self, resource_id: str, config: Dict) -> str:
        raise NotImplementedError()

    def publish_index(self, alias_name: str, index_name: str):
        raise NotImplementedError()

    def add_entries(
        self, resource_id: str, entries: List[Tuple[str, EntryMetadata, Dict]]
    ):
        raise NotImplementedError()

    def delete_entry(self, resource_id: str, entry_id: str):
        raise NotImplementedError()

    def create_empty_object(self):
        raise NotImplementedError()

    def assign_field(self, _index_entry, field_name: str, part):
        raise NotImplementedError()

    def create_empty_list(self):
        raise NotImplementedError()

    def add_to_list_field(self, elems: List, elem):
        raise NotImplementedError()


class IndexModule:
    def __init__(self):
        self.impl = IndexInterface()

    def init(self, impl: IndexInterface):
        self.impl = impl
