import logging
import time

import click

from karp.errors import KarpError, ResourceNotFoundError


_logger = logging.getLogger("karp")


def cli_error_handler(func):
    def func_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KarpError as e:
            _logger.error(e.message)
            raise click.exceptions.Exit(e.code)

    return func_wrapper


def cli_timer(func):
    def func_wrapper(*args, **kwargs):
        before_t = time.time()
        result = func(*args, **kwargs)
        click.echo("Command took: %0.1fs" % (time.time() - before_t))
        return result

    return func_wrapper
