from karp import lex, search  # noqa: D100
from karp.lex_core.value_objects.unique_id import make_unique_id
from karp.utility.time import utc_now


class GenericPreviewEntry(search.PreviewEntry):  # noqa: D101
    def __init__(  # noqa: D107
        self,
        resource_uow: lex.ResourceUnitOfWork,
        entry_transformer: search.EntryTransformer,
    ) -> None:
        super().__init__()
        self.entry_transformer = entry_transformer
        self.resource_uow = resource_uow

    def query(  # noqa: D102
        self, input_dto: search.PreviewEntryInputDto
    ) -> search.EntryPreviewDto:
        with self.resource_uow:
            resource = self.resource_uow.repo.get_by_resource_id(input_dto.resource_id)

        # entry_id = resource.id_getter()(input_dto.entry)

        lex.EntrySchema(resource.entry_json_schema).validate_entry(input_dto.entry)
        input_entry = lex.EntryDto(
            id=make_unique_id(),
            resource=input_dto.resource_id,
            version=0,
            entry=input_dto.entry,
            lastModified=utc_now(),
            lastModifiedBy=input_dto.user,
        )
        entry = self.entry_transformer.transform(input_dto.resource_id, input_entry)
        return search.EntryPreviewDto(entry=entry)
