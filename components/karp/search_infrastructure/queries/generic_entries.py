from karp import lex, search
from karp.foundation.value_objects.unique_id import make_unique_id
from karp.utility.time import utc_now


class GenericPreviewEntry(search.PreviewEntry):
    def __init__(
        self,
        resource_uow: lex.ResourceUnitOfWork,
        entry_transformer: search.EntryTransformer,
    ) -> None:
        super().__init__()
        self.entry_transformer = entry_transformer
        self.resource_uow = resource_uow

    def query(self, input_dto: search.PreviewEntryInputDto) -> search.EntryPreviewDto:
        with self.resource_uow:
            resource = self.resource_uow.repo.get_by_resource_id(input_dto.resource_id)

        # entry_id = resource.id_getter()(input_dto.entry)

        lex.EntrySchema(resource.entry_json_schema).validate_entry(input_dto.entry)
        input_entry = lex.EntryDto(
            # entry_id=entry_id,
            entity_id=make_unique_id(),
            resource=input_dto.resource_id,
            version=0,
            entry=input_dto.entry,
            last_modified=utc_now(),
            last_modified_by=input_dto.user,
        )
        entry = self.entry_transformer.transform(input_dto.resource_id, input_entry)
        return search.EntryPreviewDto(entry=entry)
