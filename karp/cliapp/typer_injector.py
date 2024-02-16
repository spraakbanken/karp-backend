from typing import Type, TypeVar  # noqa: D100, I001

import typer


T = TypeVar("T")


def inject_from_ctx(klass: Type[T], ctx: typer.Context) -> T:  # noqa: D103
    return ctx.obj["container"].get(klass)
