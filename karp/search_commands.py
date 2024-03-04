import logging

from injector import inject

from karp.lex.application import EntryQueries, ResourceQueries
from karp.search.infrastructure.es.indices import EsIndex
from karp.search.infrastructure.transformers import entry_transformer
import karp.plugins as plugins
from karp.plugins import Plugins


logger = logging.getLogger(__name__)


class SearchCommands:
    @inject
    def __init__(
        self, index: EsIndex, resource_queries: ResourceQueries, entry_queries: EntryQueries, plugins: Plugins
    ):
        super().__init__()
        self.index = index
        self.resource_queries = resource_queries
        self.entry_queries = entry_queries
        self.plugins = plugins

    def _transform(self, resource, entry):
        # TODO: make _transform only live in one place
        config = plugins.transform_config(self.plugins, resource.config)
        entry = entry.copy()
        entry.entry = plugins.transform(self.plugins, config, entry.entry)
        return entry_transformer.transform(config, entry)

    def reindex_resource(self, resource_id):
        logger.info("Reindexing resource '%s'", resource_id)
        resource = self.resource_queries.by_resource_id_optional(resource_id)
        resource_config = plugins.transform_config(self.plugins, resource.config)
        self.index.create_index(resource_id, resource_config)

        def process():
            for entry in self.entry_queries.all_entries(resource_id):
                yield self._transform(resource, entry)

        self.index.add_entries(resource_id, process())

        if resource.is_published:
            self.index.publish_index(resource_id)

    def reindex_all_resources(self):
        for resource in self.resource_queries.get_all_resources():
            self.reindex_resource(resource.resource_id)
