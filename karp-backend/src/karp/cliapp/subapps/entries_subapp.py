import collections.abc  # noqa: D100, I001
import logging
from pathlib import Path
import sys  # noqa: F401
from typing import Iterable, Optional


import json_streams
import json_streams.jsonlib
from sb_json_tools import jt_val
import typer

from tqdm import tqdm

from karp.command_bus import CommandBus
from karp import lex
from karp.lex.domain.value_objects import entry_schema

from karp.cliapp.utility import cli_error_handler, cli_timer
from karp.cliapp.typer_injector import inject_from_ctx
from karp.lex_infrastructure import SqlReadOnlyResourceRepository

logger = logging.getLogger(__name__)


subapp = typer.Typer()


@subapp.command("add")
@cli_error_handler
@cli_timer
def add_entries_to_resource(  # noqa: ANN201, D103
    ctx: typer.Context,
    resource_id: str,
    data: Path,
    chunked: bool = False,
    chunk_size: int = 1000,
    user: Optional[str] = typer.Option(None),
    message: Optional[str] = typer.Option(None),
):
    bus = inject_from_ctx(CommandBus, ctx)  # type: ignore[type-abstract]
    user = user or "local admin"
    message = message or "imported through cli"
    entries = tqdm(json_streams.load_from_file(data), desc="Adding", unit=" entries")
    if chunked:
        cmd = lex.AddEntriesInChunks(
            resourceId=resource_id,
            chunk_size=chunk_size,
            entries=entries,
            user=user,
            message=message,
        )
    else:
        cmd = lex.AddEntries(  # type: ignore[assignment]
            resourceId=resource_id,
            entries=entries,
            user=user,
            message=message,
        )
    bus.dispatch(cmd)
    typer.echo(f"Successfully added entries to {resource_id}")


@subapp.command("import")
@cli_error_handler
@cli_timer
def import_entries_to_resource(  # noqa: ANN201, D103
    ctx: typer.Context,
    resource_id: str,
    data: Path,
    chunked: bool = False,
    chunk_size: int = 1000,
    user: Optional[str] = typer.Option(None),
    message: Optional[str] = typer.Option(None),
):
    bus = inject_from_ctx(CommandBus, ctx)  # type: ignore[type-abstract]
    user = user or "local admin"
    message = message or "imported through cli"
    entries = tqdm(json_streams.load_from_file(data), desc="Importing", unit=" entries")
    if chunked:
        cmd = lex.ImportEntriesInChunks(
            resourceId=resource_id,
            chunk_size=chunk_size,
            entries=entries,
            user=user,
            message=message,
        )
    else:
        cmd = lex.ImportEntries(  # type: ignore[assignment]
            resourceId=resource_id,
            entries=entries,
            user=user,
            message=message,
        )
    bus.dispatch(cmd)
    typer.echo(f"Successfully imported entries to {resource_id}")


@subapp.command("update")
@cli_error_handler
@cli_timer
def update_entries(resource_id: str, data: Path):  # noqa: ANN201, D103
    raise NotImplementedError("")


@subapp.command("export")
@cli_error_handler
@cli_timer
def export_entries(  # noqa: ANN201, D103
    ctx: typer.Context,
    resource_id: str,
    output: typer.FileBinaryWrite = typer.Option(..., "--output", "-o"),
):
    entry_views = inject_from_ctx(lex.EntryViews, ctx=ctx)  # type: ignore[type-abstract]
    all_entries = entry_views.all_entries(resource_id=resource_id)
    logger.debug(
        "exporting entries",
        extra={"resource_id": resource_id, "type(all_entries)": type(all_entries)},
    )
    json_streams.dump(
        (entry.dict() for entry in all_entries),
        output,
    )


@subapp.command("batch")
@cli_error_handler
@cli_timer
def batch_entries(
    ctx: typer.Context,
    data: Path,
):
    """Run entry-commands in batch.

    This command expects a list with dicts with the key `cmd` that is a serialized
    command that defines `cmdtype`.

    > Example:

    > `[{"cmd": {"cmdtype": "add_entry","resourceId": "resource_a","entry": {"baseform": "sko"},"message": "add sko","user": "alice@example.com"}}]`


    """
    logger.info("run entries command in batch")
    bus = inject_from_ctx(CommandBus, ctx)  # type: ignore[type-abstract]
    entry_commands = tqdm(
        (lex.EntryCommand(**cmd) for cmd in json_streams.load_from_file(data)),
        desc="Loading",
        unit=" commands",
    )
    cmd = lex.ExecuteBatchOfEntryCommands(commands=entry_commands)

    bus.dispatch(cmd)


class Counter(collections.abc.Generator):  # noqa: D101
    def __init__(self, sink) -> None:  # noqa: D107
        self._counter: int = 0
        self._sink = sink

    @property
    def counter(self) -> int:  # noqa: D102
        return self._counter

    def send(self, value):  # noqa: ANN201, D102
        self._counter += 1
        self._sink.send(value)

    def throw(self, typ=None, val=None, tb=None):  # noqa: ANN201, D102
        raise StopIteration


@subapp.command("validate")
@cli_error_handler
@cli_timer
def validate_entries(  # noqa: ANN201, D103
    ctx: typer.Context,
    path: Optional[Path] = typer.Argument(None),
    config_path: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="resource config",
    ),
    resource_id_raw: Optional[str] = typer.Option(None, "--resource_id"),
    as_import: bool = typer.Option(False, "--as-import"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="file to write to"),
):
    """Validate entries without adding or importing them.

    You can either read the configuration from the database by specifing `--resource_id=<RESOURCE ID>`
    or supply an external config with `--config=<PATH>`.

    By default, this command supposes that the entries are in raw mode (like `add` works),
    to use the format the `import` uses please add the `--as-import` flag.
    """
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
        repo = inject_from_ctx(SqlReadOnlyResourceRepository, ctx=ctx)
        if resource := repo.get_by_resource_id(resource_id_raw):
            config = resource.config
        else:
            typer.echo(f"Can't find resource '{resource_id_raw}'", err=True)
            raise typer.Exit(302)
    else:
        typer.echo("You must provide either '--resource_id' or '--config/-c'", err=True)
        raise typer.Exit(code=300)

    allow_additional_properties = config.get("additionalProperties", True)
    schema = entry_schema.create_entry_json_schema(config["fields"], allow_additional_properties)

    error_code = 0

    entries: Iterable[dict] = json_streams.load_from_file(path, use_stdin_as_default=True)
    if as_import:
        entries = (import_entry["entry"] for import_entry in entries)
    with json_streams.sink_from_file(
        err_output, use_stderr_as_default=True
    ) as error_sink, json_streams.sink_from_file(
        output, use_stdout_as_default=True
    ) as correct_sink:
        error_counter = Counter(error_sink)
        jt_val.processing_validate(
            schema,
            tqdm(
                entries,
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


def init_app(app):  # noqa: ANN201, D103
    app.add_typer(subapp, name="entries")
