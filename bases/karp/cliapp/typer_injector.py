from typing import Type, TypeVar

import typer


T = TypeVar("T")


def inject_from_ctx(klass: Type[T], ctx: typer.Context) -> T:
    return ctx.obj["container"].get(klass)
