from typing import Type, TypeVar

import typer


T = TypeVar('T')


def inject_from_ctx(klass: Type[T], ctx: typer.Context) -> T:
    return ctx.obj['app_context'].container.get(klass)
