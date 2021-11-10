import typing

from karp.search.domain.search_service import IndexEntry
from karp.search.application.transformers import PreProcessor, EntryTransformer


class GenericPreProcessor(PreProcessor):
    def __init__(
        self,
        entry_transformer: EntryTransformer,
    ):
        super().__init__()
        self.entry_transformer = entry_transformer

def pre_process_resource(
    resource_id: str,
) -> typing.Iterable[IndexEntry]:
    with ctx.resource_uow as uw:
        resource = uw.repo.by_resource_id(resource_id)
        if not resource:
            raise errors.ResourceNotFound(resource_id=resource_id)

    with ctx.entry_uows.get(resource_id) as uw:
        for entry in uw.repo.all_entries():
            yield transform_to_search_service_entry(resource, entry, ctx)

