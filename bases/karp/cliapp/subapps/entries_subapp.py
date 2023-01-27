import collections.abc
import logging
from pathlib import Path
import sys
from typing import Optional


import json_streams
import json_streams.jsonlib
from sb_json_tools import jt_val
import typer

# from tabulate import tabulate
from tqdm import tqdm

from karp.foundation.commands import CommandBus
from karp import lex
from karp.utility import json_schema

# from karp.lex.domain.errors import ResourceAlreadyPublished

from karp.cliapp.utility import cli_error_handler, cli_timer
from karp.cliapp.typer_injector import inject_from_ctx

logger = logging.getLogger(__name__)


subapp = typer.Typer()


@subapp.command("add")
@cli_error_handler
@cli_timer
def add_entries_to_resource(
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
    entries = tqdm(json_streams.load_from_file(data), desc="Adding", unit=" entries")
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
    typer.echo(f"Successfully added entries to {resource_id}")


@subapp.command("import")
@cli_error_handler
@cli_timer
def import_entries_to_resource(
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
    entries = tqdm(json_streams.load_from_file(data), desc="Adding", unit=" entries")
    if chunked:
        cmd = lex.ImportEntriesInChunks(
            resource_id=resource_id,
            chunk_size=chunk_size,
            entries=entries,
            user=user,
            message=message,
        )
    else:
        cmd = lex.ImportEntries(
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
    raise NotImplementedError("")


@subapp.command("export")
@cli_error_handler
@cli_timer
def export_entries(
    ctx: typer.Context,
    resource_id: str,
    output: typer.FileBinaryWrite = typer.Option(..., "--output", "-o"),
):
    entry_views = inject_from_ctx(lex.EntryViews, ctx=ctx)
    all_entries = entry_views.all_entries(resource_id=resource_id)
    logger.debug(
        "exporting entries",
        extra={"resource_id": resource_id, "type(all_entries)": type(all_entries)},
    )
    json_streams.dump(
        (entry.dict() for entry in all_entries),
        output,
    )


class Counter(collections.abc.Generator):
    def __init__(self, sink) -> None:
        self._counter: int = 0
        self._sink = sink

    @property
    def counter(self) -> int:
        return self._counter

    def send(self, value):
        self._counter += 1
        self._sink.send(value)

    def throw(self, typ=None, val=None, tb=None):
        raise StopIteration


@subapp.command("validate")
@cli_error_handler
@cli_timer
def validate_entries(
    ctx: typer.Context,
    path: Optional[Path] = typer.Argument(None),
    config_path: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="resource config",
    ),
    resource_id_raw: Optional[str] = typer.Option(None, "--resource_id"),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="file to write to"
    ),
):
    typer.echo(f"reading from {path or 'stdin'} ...", err=True)

    if not output and path:
        output = Path(f"{path}.v6.jsonl")

    err_output = Path(f"{output}.errors.jsonl")

    if config_path and resource_id_raw:
        typer.echo("You can't provide both '--resource_id' and '--config/-c'", err=True)
        raise typer.Exit(301)

    if config_path:
        config = json_streams.jsonlib.load_from_file(config_path)
    elif resource_id_raw:
        repo = inject_from_ctx(lex.ReadOnlyResourceRepository, ctx=ctx)
        if resource := repo.get_by_resource_id(resource_id_raw):
            config = resource.config
        else:
            typer.echo(f"Can't find resource '{resource_id_raw}'", err=True)
            raise typer.Exit(302)
    else:
        typer.echo("You must provide either '--resource_id' or '--config/-c'", err=True)
        raise typer.Exit(code=300)

    schema = json_schema.create_entry_json_schema(config["fields"])

    error_code = 0

    with json_streams.sink_from_file(
        err_output, use_stderr_as_default=True
    ) as error_sink, json_streams.sink_from_file(
        output, use_stdout_as_default=True
    ) as correct_sink:
        error_counter = Counter(error_sink)
        # error_counter.send(None)
        jt_val.processing_validate(
            schema,
            tqdm(
                json_streams.load_from_file(path, use_stdin_as_default=True),
                desc="Validating",
                unit=" entries",
            ),
            on_ok=correct_sink,
            on_error=error_counter,
        )
        if error_counter.counter > 0:
            error_code = 130
            typer.echo(
                f'{error_counter.counter} entries failed validation, see "{err_output}"',
                err=True,
            )

    if error_code:
        raise typer.Exit(error_code)


def init_app(app):
    app.add_typer(subapp, name="entries")
