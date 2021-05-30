from karp.services import messagebus, unit_of_work


def bootstrap(
    resource_uow: unit_of_work.ResourceUnitOfWork,
    entry_uows: unit_of_work.EntriesUnitOfWork,
) -> messagebus.MessageBus:
    return messagebus.MessageBus(
        resource_uow=resource_uow,
        entry_uows=entry_uows,
    )
