import logging

from injector import inject

import karp.plugins as plugins
from karp.lex.application import EntryQueries, ResourceQueries
from karp.plugins import Plugins
from karp.search.infrastructure.es.indices import EsIndex
from karp.search.infrastructure.transformers import entry_transformer

logger = logging.getLogger(__name__)


class SearchCommands:
    @inject
    def __init__(
        self,
        index: EsIndex,
        resource_queries: ResourceQueries,
        entry_queries: EntryQueries,
        plugins: Plugins,
    ):
        super().__init__()
        self.index = index
        self.resource_queries = resource_queries
        self.entry_queries = entry_queries
        self.plugins = plugins

    def reindex_resource(self, resource_id, remove_old_index):
        logger.info("Reindexing resource '%s'", resource_id)
        resource = self.resource_queries.by_resource_id(resource_id, expand_plugins=plugins.INDEXED)

        # create and add data to new index without touching the old alias
        index_name = self.index.create_index(resource_id, resource.config, create_alias=False)
        all_entries = self.entry_queries.all_entries(resource_id, expand_plugins=plugins.INDEXED)
        self.index.add_entries(index_name, (entry_transformer.transform(entry) for entry in all_entries))

        if remove_old_index:
            self.index.delete_index(resource_id)

        # now when the data adding is done, point alias to the new index
        self.index.create_alias(resource_id, index_name)

    def reindex_all_resources(self, remove_old_index):
        for resource in self.resource_queries.get_all_resources():
            self.reindex_resource(resource.resource_id, remove_old_index)
