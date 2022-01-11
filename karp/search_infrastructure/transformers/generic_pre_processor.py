import typing

from karp.lex.application.queries import EntryViews
from karp.search.application.repositories import IndexEntry
from karp.search.application.transformers import PreProcessor, EntryTransformer


class GenericPreProcessor(PreProcessor):
    def __init__(
        self,
        entry_transformer: EntryTransformer,
        entry_views: EntryViews,
    ):
        super().__init__()
        self.entry_transformer = entry_transformer
        self.entry_views = entry_views

    def process(
        self,
        resource_id: str,
    ) -> typing.Iterable[IndexEntry]:
        for entry in self.entry_views.all_entries(resource_id):
            yield self.entry_transformer.transform(resource_id, entry)
