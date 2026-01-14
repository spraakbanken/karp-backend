from karp.foundation.json import get_path
from karp.lex.application import entry_queries, resource_queries

from .plugin import Plugin


class ResourcePlugin(Plugin):
    def output_config(self, resource, path=""):
        resource_dto = resource_queries.by_resource_id_optional(resource)
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
        data = entry_queries.all_entries(resource)
        return [get_path(path, entry.entry) for entry in data]
