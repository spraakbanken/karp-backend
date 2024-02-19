from pathlib import Path  # noqa: I001
from typing import Optional

import json_streams
import typer

from karp import search
from karp.cliapp.typer_injector import inject_from_ctx
from karp.search_infrastructure.queries import Es6SearchService


subapp = typer.Typer()


@subapp.command()
def resource(
    ctx: typer.Context,
    resource_id: str,
    output: Optional[Path] = typer.Option(None, help="Path to write to. Defaults to stdout."),
):
    search_service = inject_from_ctx(Es6SearchService, ctx)
    query_request = search.QueryRequest(resource_ids=[resource_id])
    json_streams.dump_to_file(
        search_service.query(query_request),
        output,
        use_stdout_as_default=True,
    )


def init_app(app: typer.Typer) -> None:
    app.add_typer(subapp, name="query")
