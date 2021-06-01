from karp.services import messagebus, unit_of_work
from karp.infrastructure.sql import sql_unit_of_work


def bootstrap(
    resource_uow: unit_of_work.ResourceUnitOfWork = None,
    entry_uows: unit_of_work.EntriesUnitOfWork = None,
) -> messagebus.MessageBus:
    if resource_uow is None:
        resource_uow = sql_unit_of_work.SqlResourceUnitOfWork()
    if entry_uows is None:
        entry_uows = unit_of_work.EntriesUnitOfWork()
    return messagebus.MessageBus(
        resource_uow=resource_uow,
        entry_uows=entry_uows,
    )
