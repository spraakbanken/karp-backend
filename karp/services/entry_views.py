import typing

from karp.domain import model
from karp.utility import unique_id
from . import context


def get_by_id(
    resource_id: str,
    entry_uuid: unique_id.UniqueId,
    ctx: context.Context
) -> typing.Optional[model.Resource]:
    with ctx.entry_uows.get_uow(resource_id) as uow:
        return uow.repo.by_id(entry_uuid)
