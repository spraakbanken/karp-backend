from karp.domain.commands import CreateResource
from karp.domain.model import Resource

# from karp.domain.model import Issue, IssueReporter
from karp.infrastructure.unit_of_work import UnitOfWork


def create_resource(cmd: CreateResource, uow: UnitOfWork):
    resource = Resource(
        entity_id=cmd.id,
        resource_id=cmd.resource_id,
        name=cmd.name,
        config=cmd.config,
        message=cmd.message,
        last_modified_by=cmd.created_by,
    )

    with uow:
        uow.repo.put(resource)
        uow.commit()
