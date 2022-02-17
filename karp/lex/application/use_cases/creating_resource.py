
from karp.lex.application.queries.resources import ResourceDto
from karp.lex.application.repositories import (
    EntryUowRepositoryUnitOfWork,
    ResourceUnitOfWork,
)
from karp.lex.domain import entities
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
            existing_resource = uow.resources.get_by_resource_id_optional(
                    input_dto.resource_id)
            if existing_resource and not existing_resource.discarded and existing_resource.entity_id != input_dto.entity_id:
                raise errors.IntegrityError(
                    f"Resource with resource_id='{input_dto.resource_id}' already exists."
                )
            resource = entities.create_resource(
                entity_id=input_dto.entity_id,
                resource_id=input_dto.resource_id,
                config=input_dto.config,
                message=input_dto.message,
                entry_repo_id=input_dto.entry_repo_id,
                created_at=input_dto.timestamp,
                created_by=input_dto.user,
                name=input_dto.name,
            )

            uow.repo.save(resource)
            uow.commit()
        return ResourceDto(
            **resource.dict()
        )


