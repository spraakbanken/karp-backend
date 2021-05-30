from karp.services import messagebus, unit_of_work


def bootstrap(
    resource_uow: unit_of_work.ResourceUnitOfWork,
) -> messagebus.MessageBus:
    return messagebus.MessageBus(
        resource_uow=resource_uow,
    )
