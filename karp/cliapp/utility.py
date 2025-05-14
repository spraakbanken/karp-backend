import functools
import logging
import time

import typer


def cli_error_handler(func):
    @functools.wraps(func)
    def func_wrapper(*args, **kwargs):
        from karp.lex.domain.errors import LexDomainError
        from karp.main.errors import KarpError

        logger = logging.getLogger("karp")

        try:
            return func(*args, **kwargs)
        except KarpError as e:
            logger.error(e.message)
            raise typer.Exit(e.code) from None
        except LexDomainError as e:
            logger.error(str(e))
            raise typer.Exit(1) from None

    return func_wrapper


def cli_timer(func):
    @functools.wraps(func)
    def func_wrapper(*args, **kwargs):
        before_t = time.time()
        result = func(*args, **kwargs)
        typer.echo("Command took: %0.1fs" % (time.time() - before_t))
        return result

    return func_wrapper
