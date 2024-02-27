from typing import Type, TypeVar  # noqa: I001

import typer


T = TypeVar("T")


def inject_from_ctx(klass: Type[T], ctx: typer.Context) -> T:
    return ctx.obj["injector"].get(klass)
