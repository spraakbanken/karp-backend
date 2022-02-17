from karp.lex.application.queries.resources import ResourceDto
from karp.lex.application.repositories import (
    EntryUowRepositoryUnitOfWork,
    ResourceUnitOfWork,
)
from karp.lex.domain.commands import CreateResource


class CreatingResource:
    def __init__(
        self,
        resource_uow: ResourceUnitOfWork,
        entry_repo_uow: EntryUowRepositoryUnitOfWork,
    ):
        self.resource_uow = resource_uow
        self.entry_repo_uow = entry_repo_uow

    def execute(self, input_dto: CreateResource) -> ResourceDto:
        with self.entry_repo_uow as entry_repo_uow:
            entry_repo_exist = entry_repo_uow.repo.get_by_id_optional(input_dto.entry_repo_id)
            if not entry_repo_exist:
                raise ValueError(f"entry repo '{input_dto.entry_repo_id}' does not exist.")
        with self.resource_uow as uow:
            existing_resource = uow.resources.by_resource_id_optional(
                    cmd.resource_id)
            if existing_resource and not existing_resource.discarded and existing_resource.entity_id != cmd.entity_id:
                raise errors.IntegrityError(
                    f"Resource with resource_id='{cmd.resource_id}' already exists."
                )
            resource = entities.create_resource(
                entity_id=cmd.entity_id,
                resource_id=cmd.resource_id,
                config=cmd.config,
                message=cmd.message,
                entry_repo_id=cmd.entry_repo_id,
                created_at=cmd.timestamp,
                created_by=cmd.created_by,
                name=cmd.name,
            )

            uow.repo.save(resource)
            uow.commit()


        if not input_dto.entry_repo_id:
            create_entry_repo = commands.CreateEntryRepository(
                repository_type='default',
                user=user,
                **input_dto.dict()
            )
            bus.dispatch(create_entry_repo)
            new_resource.entry_repo_id = create_entry_repo.entity_id
