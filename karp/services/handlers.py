from karp.domain import commands, model, errors

# from karp.domain.model import Issue, IssueReporter
from . import context



def update_resource(cmd: commands.UpdateResource, uow: UnitOfWork):
    with uow:
        resource = uow.repo.by_resource_id(cmd.resource_id)
        found_changes = False
        if resource.name != cmd.name:
            resource.name = cmd.name
            found_changes = True
        if resource.config != cmd.config:
            resource.config = cmd.config
            found_changes = True
        if found_changes:
            resource.stamp(
                user=cmd.user,
                message=cmd.message,
                timestamp=cmd.timestamp,
            )
            uow.repo.update(resource)
        uow.commit()


# Entry handlers


def add_entry(cmd: commands.AddEntry, uow: UnitOfWork):
    with uow:
        # resource = uow.repo.by_resource_id(cmd.resource_id)
        # with unit_of_work(using=resource.entry_repository) as uow2:
        existing_entry = uow.repo.by_entry_id(cmd.entry_id)
        if (
            existing_entry
            and not existing_entry.discarded
            and existing_entry.id != cmd.id
        ):
            raise errors.IntegrityError(
                f"An entry with entry_id '{cmd.entry_id}' already exists."
            )
        entry = model.Entry(
            entity_id=cmd.id,
            entry_id=cmd.entry_id,
            resource_id=cmd.resource_id,
            body=cmd.body,
            message=cmd.message,
            last_modified=cmd.timestamp,
            last_modified_by=cmd.user,
        )
        # uow2.repo.put(entry)
        # uow2.commit()
        uow.repo.put(entry)
        uow.commit()
