import logging
from pathlib import Path
from typing import Optional

import json_streams
import typer
from tabulate import tabulate
from tqdm import tqdm

from karp.foundation.commands import CommandBus
from karp import lex
from karp.lex.domain import commands

# from karp.lex.domain.errors import ResourceAlreadyPublished

from karp.cliapp.utility import cli_error_handler, cli_timer
from karp.cliapp.typer_injector import inject_from_ctx

logger = logging.getLogger("karp")


subapp = typer.Typer()


@subapp.command("import")
@cli_error_handler
@cli_timer
def import_resource(
    ctx: typer.Context,
    resource_id: str,
    # version: Optional[int],
    data: Path,
    chunked: bool = False,
    chunk_size: int = 1000,
    user: Optional[str] = typer.Option(None),
    message: Optional[str] = typer.Option(None),
):
    bus = inject_from_ctx(CommandBus, ctx)
    user = user or "local admin"
    message = message or "imported through cli"
    entries = tqdm(json_streams.load_from_file(data), desc="Importing", unit=" entries")
    if chunked:
        cmd = lex.AddEntriesInChunks(
            resource_id=resource_id,
            chunk_size=chunk_size,
            entries=entries,
            user=user,
            message=message,
        )
    else:
        cmd = lex.AddEntries(
            resource_id=resource_id,
            entries=entries,
            user=user,
            message=message,
        )
    bus.dispatch(cmd)
    typer.echo(f"Successfully imported entries to {resource_id}")


@subapp.command("update")
@cli_error_handler
@cli_timer
def update_entries(resource_id: str, data: Path):
    updated_entries = entries.update_entries(
        resource_id, json_streams.load_from_file(data)
    )


@subapp.command("export")
@cli_error_handler
@cli_timer
def export_entries(
    ctx: typer.Context,
    resource_id: str,
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
):
    entry_views = inject_from_ctx(lex.EntryViews, ctx=ctx)
    json_streams.dump_to_file(
        tqdm(
            entry_views.all_entries(resource_id),
            desc="Exporting",
            unit=" entries",
        ),
        output,
        use_stdout_as_default=None,
    )


def init_app(app):
    app.add_typer(subapp, name="entries")
