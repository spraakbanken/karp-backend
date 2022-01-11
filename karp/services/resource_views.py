from typing import List

from karp.domain import model

from . import context


def get_published_resources(ctx: context.Context) -> List[model.Resource]:
    with ctx.resource_uow:
        return ctx.resource_uow.resources.get_published_resources()
