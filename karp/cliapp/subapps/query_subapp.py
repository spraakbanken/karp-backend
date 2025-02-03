from pathlib import Path  # noqa: I001
from typing import Optional

import json_arrays
import typer

from karp import search
from karp.cliapp.typer_injector import inject_from_ctx
from karp.lex.application import SearchQueries


subapp = typer.Typer()


@subapp.command()
def resource(
    ctx: typer.Context,
    resource_id: str,
    output: Optional[Path] = typer.Option(None, help="Path to write to. Defaults to stdout."),
):
    search_queries = inject_from_ctx(SearchQueries, ctx)
    query_request = search.QueryRequest(resource_ids=[resource_id])
    json_arrays.dump_to_file(
        search_queries.query(query_request),
        output,
        use_stdout_as_default=True,
    )


def init_app(app: typer.Typer) -> None:
    app.add_typer(subapp, name="query")
