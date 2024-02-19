import logging

from karp.lex_infrastructure import EntryQueries, ResourceQueries
from karp.search_infrastructure.repositories.es6_indicies import Es6Index
from karp.search_infrastructure.transformers import entry_transformer

logger = logging.getLogger(__name__)


class SearchCommands:
    def __init__(
        self, index: Es6Index, resource_queries: ResourceQueries, entry_queries: EntryQueries
    ):
        super().__init__()
        self.index = index
        self.resource_queries = resource_queries
        self.entry_queries = entry_queries

    def reindex_resource(self, resource_id):
        logger.info("Reindexing resource '%s'", resource_id)
        resource = self.resource_queries.by_resource_id_optional(resource_id)
        self.index.create_index(resource_id, resource.config)

        def process():
            for entry in self.entry_queries.all_entries(resource_id):
                yield entry_transformer.transform(resource, entry)

        self.index.add_entries(resource_id, process())

        if resource.is_published:
            self.index.publish_index(resource_id)

    def reindex_all_resources(self):
        for resource in self.resource_queries.get_all_resources():
            self.reindex_resource(resource.resource_id)
