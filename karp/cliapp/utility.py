import functools  # noqa: D100, I001
import logging
import time

import typer

from karp.main.errors import KarpError

logger = logging.getLogger("karp")


def cli_error_handler(func):  # noqa: ANN201, D103
    @functools.wraps(func)
    def func_wrapper(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
        try:
            return func(*args, **kwargs)
        except KarpError as e:
            logger.error(e.message)
            raise typer.Exit(e.code)  # noqa: B904

    return func_wrapper


def cli_timer(func):  # noqa: ANN201, D103
    @functools.wraps(func)
    def func_wrapper(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
        before_t = time.time()
        result = func(*args, **kwargs)
        typer.echo("Command took: %0.1fs" % (time.time() - before_t))
        return result

    return func_wrapper
