import logging

from karp.search.generic_resources import GenericResourceViews
from karp.search_infrastructure import GenericPreProcessor
from karp.search_infrastructure.repositories.es6_indicies import Es6Index

logger = logging.getLogger(__name__)


class SearchCommands:
    def __init__(
        self,
        index: Es6Index,
        resource_views: GenericResourceViews,
        pre_processor: GenericPreProcessor,
    ):
        super().__init__()
        self.index = index
        self.resource_views = resource_views
        self.pre_processor = pre_processor

    def reindex_resource(self, resource_id):
        logger.debug("Reindexing resource '%s'", resource_id)
        self.index.create_index(
            resource_id,
            self.resource_views.get_resource_config(resource_id),
        )
        self.index.add_entries(resource_id, self.pre_processor.process(resource_id))
