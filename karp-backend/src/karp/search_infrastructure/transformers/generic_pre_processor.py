import logging  # noqa: D100, I001
import typing

from karp.lex_infrastructure import GenericEntryViews
from karp.search.application.repositories import IndexEntry
from karp.search_infrastructure.transformers.generic_entry_transformer import GenericEntryTransformer

logger = logging.getLogger(__name__)


class GenericPreProcessor:
    def __init__(  # noqa: D107, ANN204
        self,
        entry_transformer: GenericEntryTransformer,
        entry_views: GenericEntryViews,
    ):
        super().__init__()
        self.entry_transformer = entry_transformer
        self.entry_views = entry_views

    def process(  # noqa: D102
        self,
        resource_id: str,
    ) -> typing.Iterable[IndexEntry]:
        logger.debug(
            "processing entries for resource", extra={"resource_id": resource_id}
        )

        for entry in self.entry_views.all_entries(resource_id):
            logger.debug(
                "processing entry", extra={"entry": entry, "resource_id": resource_id}
            )
            yield self.entry_transformer.transform(resource_id, entry)
