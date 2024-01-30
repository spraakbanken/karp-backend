import logging

from karp.lex.application.repositories import EntryUnitOfWork
from karp.lex.domain.errors import EntryNotFound, ResourceNotFound
from karp.lex_core.value_objects import unique_id
from karp.search import IndexUnitOfWork
from karp.search.generic_resources import GenericResourceViews
from karp.search_infrastructure import GenericPreProcessor
from karp.timings import utc_now

logger = logging.getLogger(__name__)


class SearchCommands:
    def __init__(
        self,
        index_uow: IndexUnitOfWork,
        resource_views: GenericResourceViews,
        pre_processor: GenericPreProcessor,
    ):
        super().__init__()
        self.index_uow = index_uow
        self.resource_views = resource_views
        self.pre_processor = pre_processor

    def reindex_resource(self, resource_id):
        logger.debug("Reindexing resource '%s'", resource_id)
        with self.index_uow as uw:
            uw.repo.create_index(
                resource_id,
                self.resource_views.get_resource_config(resource_id),
            )
            uw.repo.add_entries(resource_id, self.pre_processor.process(resource_id))
            uw.commit()
