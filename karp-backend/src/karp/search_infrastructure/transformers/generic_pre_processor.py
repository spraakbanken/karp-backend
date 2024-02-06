import logging  # noqa: D100, I001
import typing

from karp.lex_infrastructure import GenericEntryViews, ResourceQueries
from karp.search.application.repositories import IndexEntry
from karp.search_infrastructure.transformers import entry_transformer

logger = logging.getLogger(__name__)


class GenericPreProcessor:
    def __init__(self, entry_views: GenericEntryViews, resource_queries: ResourceQueries):
        super().__init__()
        self.entry_views = entry_views
        self.resource_queries = resource_queries

    def process(  # noqa: D102
        self,
        resource_id: str,
    ) -> typing.Iterable[IndexEntry]:
        logger.debug("processing entries for resource", extra={"resource_id": resource_id})

        for entry in self.entry_views.all_entries(resource_id):
            logger.debug("processing entry", extra={"entry": entry, "resource_id": resource_id})
            resource = self.resource_queries.by_resource_id_optional(resource_id)
            yield entry_transformer.transform(resource, entry)
