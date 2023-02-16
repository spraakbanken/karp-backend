from pathlib import Path  # noqa: D100, I001
from typing import Optional

import json_streams
import typer

from karp import search
from karp.cliapp.typer_injector import inject_from_ctx


subapp = typer.Typer()


@subapp.command()
def resource(  # noqa: ANN201, D103
    ctx: typer.Context,
    resource_id: str,
    output: Optional[Path] = typer.Option(
        None, help="Path to write to. Defaults to stdout."
    ),
):
    search_service = inject_from_ctx(search.SearchService, ctx)
    query_request = search.QueryRequest(resource_ids=[resource_id])
    json_streams.dump_to_file(
        search_service.query(query_request),
        output,
        use_stdout_as_default=True,
    )


def init_app(app: typer.Typer) -> None:  # noqa: D103
    app.add_typer(subapp, name="query")
