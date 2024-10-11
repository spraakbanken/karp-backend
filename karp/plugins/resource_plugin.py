from injector import inject

from karp.foundation.json import get_path
from karp.lex.application import EntryQueries, ResourceQueries

from .plugin import Plugin


class ResourcePlugin(Plugin):
    @inject
    def __init__(self, resources: ResourceQueries, entries: EntryQueries):
        self.resources = resources
        self.entries = entries

    def output_config(self, resource, path=""):
        resource_dto = self.resources.by_resource_id_optional(resource)
        if resource_dto:
            config = resource_dto.config.field_config(path)
            nesting_level = resource_dto.config.nesting_level(path)
            if nesting_level == 1:
                config = config.update(collection=True)
            elif nesting_level > 1:
                raise ValueError(f"Resource plugin can't return nested collection {path}")
            return config
        else:
            # Return no fields for now - the user must run 'karp-cli resource reindex' later
            return {"type": "object", "fields": {}, "collection": True}

    def generate(self, resource, path=""):
        data = self.entries.all_entries(resource)
        return [get_path(path, entry.entry) for entry in data]
