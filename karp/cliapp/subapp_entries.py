import logging
from pathlib import Path
from typing import Optional

import json_streams
import typer
from tabulate import tabulate
from tqdm import tqdm

# from karp.application.services import entries
from karp.lex.domain import commands
# from karp.lex.domain.errors import ResourceAlreadyPublished

from .utility import cli_error_handler, cli_timer
from .typer_injector import inject_from_ctx

logger = logging.getLogger("karp")


subapp = typer.Typer()


@subapp.command("import")
@cli_error_handler
@cli_timer
def import_resource(
    resource_id: str,
    version: Optional[int],
    data: Path,
    ctx: typer.Context,
):
    cmd = commands.AddEntries(
        resource_id=resource_id,
        entries=tqdm(
            json_streams.load_from_file(data), desc="Importing", unit=" entries"
        ),
        user="local admin",
        message="imported through cli",
    )
    app_config.bus.handle(cmd)
    typer.echo(f"Successfully imported entries to {resource_id}")


@subapp.command("update")
@cli_error_handler
@cli_timer
def update_entries(resource_id: str, data: Path):
    updated_entries = entries.update_entries(
        resource_id, json_streams.load_from_file(data)
    )


def init_app(app):
    app.add_typer(subapp, name="entries")
