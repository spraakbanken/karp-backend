import typing

from karp.lex.application.queries import GetEntryRepositoryId
from karp.lex.application.repositories import EntryUowRepositoryUnitOfWork
from karp.search.application.repositories import IndexEntry
from karp.search.application.transformers import PreProcessor, EntryTransformer


class GenericPreProcessor(PreProcessor):
    def __init__(
        self,
        entry_transformer: EntryTransformer,
        get_entry_repo_id: GetEntryRepositoryId,
        entry_uow_repo_uow: EntryUowRepositoryUnitOfWork,
    ):
        super().__init__()
        self.entry_transformer = entry_transformer
        self.get_entry_repo_id = get_entry_repo_id
        self.entry_uow_repo_uow = entry_uow_repo_uow

    def process(
        self,
        resource_id: str,
    ) -> typing.Iterable[IndexEntry]:
        entry_repo_id = self.get_entry_repo_id.query(resource_id)

        with self.entry_uow_repo_uow:
            with self.entry_uow_repo_uow.repo.get_by_id(entry_repo_id) as uw:
                for entry in uw.repo.all_entries():
                    yield self.entry_transformer.transform(resource_id, entry)
