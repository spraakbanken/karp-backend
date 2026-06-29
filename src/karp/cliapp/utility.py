import functools
import itertools
import logging
import time
from typing import Sequence

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


def tabulate(rows: Sequence[Sequence[object]], headers: Sequence[str] = ()):
    """
    Simple tabulation utility. Will break in undefined ways if length of each
    row and headers are not the same.
    """
    # rows are used twice, do this to make generators work as input
    rows = list(rows)

    cols: list[list[object]] = [[] for _ in range(0, len(rows[0]))]
    widths: list[int] = []
    start_end_sep: list[str] = []
    for tmp in itertools.chain((headers,), rows):
        for idx, val in enumerate(tmp):
            cols[idx].append(val)

    for col in cols:
        col_width = max((len(str(x)) for x in col))
        widths.append(col_width)
        start_end_sep.append("-" * col_width)

    start_end_sep_str = "  ".join(start_end_sep)

    row: list[str] = []
    for width, val in zip(widths, headers, strict=False):
        row.append(f"{val:<{width}}")
    res: list[str] = []
    res.append("  ".join(row))

    res.append(start_end_sep_str)
    for columns in rows:
        row = []
        for width, val in zip(widths, columns, strict=False):
            row.append(f"{val:<{width}}")
        res.append("  ".join(row))
    res.append(start_end_sep_str)

    return "\n".join(res)
