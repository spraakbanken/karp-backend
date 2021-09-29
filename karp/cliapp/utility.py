import functools
import logging
import time

import typer

from karp.errors import KarpError, ResourceNotFoundError

logger = logging.getLogger("karp")


def cli_error_handler(func):
    @functools.wraps(func)
    def func_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KarpError as e:
            logger.error(e.message)
            raise typer.Exit(e.code)

    return func_wrapper


def cli_timer(func):
    @functools.wraps(func)
    def func_wrapper(*args, **kwargs):
        before_t = time.time()
        result = func(*args, **kwargs)
        typer.echo("Command took: %0.1fs" % (time.time() - before_t))
        return result

    return func_wrapper
