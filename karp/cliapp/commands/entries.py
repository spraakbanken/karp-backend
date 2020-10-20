
import logging
from pathlib import Path
from typing import Optional

import typer

from tabulate import tabulate

from karp.application.services import entries
from karp.errors import ResourceAlreadyPublished

from ..utility import cli_error_handler, cli_timer

logger = logging.getLogger("karp")


subapp = typer.Typer()


@subapp.command("import")
@cli_error_handler
@cli_timer
def import_resource(resource_id: str, version: Optional[int], data: Path):
    count = entries.add_entries_from_file(resource_id, version, data)
    typer.echo(f"Added {count} entries to {resource_id}, version {version}")


def init_app(app):
    app.add_typer(subapp, name="entries")
