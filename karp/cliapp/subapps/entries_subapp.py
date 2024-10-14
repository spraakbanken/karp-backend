import collections.abc  # noqa: I001
import logging
from pathlib import Path
from typing import Iterable, Optional


import json_arrays
import json_arrays.jsonlib
from sb_json_tools import jt_val
import typer

from tqdm import tqdm

from karp.entry_commands import EntryCommands
from karp.lex.domain.value_objects import entry_schema, ResourceConfig

from karp.cliapp.utility import cli_error_handler, cli_timer
from karp.cliapp.typer_injector import inject_from_ctx
from karp.lex.application import ResourceQueries, EntryQueries

logger = logging.getLogger(__name__)


subapp = typer.Typer()


@subapp.command("add")
@cli_error_handler
@cli_timer
def add_entries_to_resource(
    ctx: typer.Context,
    resource_id: str,
    data: Path,
    chunked: bool = False,
    chunk_size: int = 1000,
    user: Optional[str] = typer.Option(None),
    message: Optional[str] = typer.Option(None),
):
    entry_commands = inject_from_ctx(EntryCommands, ctx)
    user = user or "local admin"
    message = message or "imported through cli"
    entries = tqdm(json_arrays.load_from_file(data), desc="Adding", unit=" entries")
    if chunked:
        entry_commands.add_entries_in_chunks(
            resource_id=resource_id,
            chunk_size=chunk_size,
            entries=entries,
            user=user,
            message=message,
        )
    else:
        entry_commands.add_entries(
            resource_id=resource_id,
            entries=entries,
            user=user,
            message=message,
        )
    typer.echo(f"Successfully added entries to {resource_id}")


@subapp.command("import")
@cli_error_handler
@cli_timer
def import_entries_to_resource(
    ctx: typer.Context,
    resource_id: str,
    data: Path,
    chunked: bool = False,
    chunk_size: int = 1000,
    user: Optional[str] = typer.Option(None),
    message: Optional[str] = typer.Option(None),
):
    entry_commands = inject_from_ctx(EntryCommands, ctx)
    user = user or "local admin"
    message = message or "imported through cli"
    entries = tqdm(json_arrays.load_from_file(data), desc="Importing", unit=" entries")
    if chunked:
        entry_commands.import_entries_in_chunks(
            resource_id=resource_id,
            chunk_size=chunk_size,
            entries=entries,
            user=user,
            message=message,
        )
    else:
        entry_commands.import_entries(
            resource_id=resource_id,
            entries=entries,
            user=user,
            message=message,
        )
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
    expand_plugins: bool = True,
):
    resource_queries = inject_from_ctx(ResourceQueries, ctx=ctx)
    entry_queries = inject_from_ctx(EntryQueries, ctx=ctx)
    resource = resource_queries.by_resource_id(resource_id)
    entries = entry_queries.all_entries(resource_id=resource_id, expand_plugins=expand_plugins)
    logger.debug(
        "exporting entries",
        extra={"resource_id": resource_id, "type(all_entries)": type(entries)},
    )

    json_arrays.dump(
        (entry.dict() for entry in entries),
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

    > `[{"cmd": {"cmdtype": "add_entry","resource_id": "resource_a","entry": {"baseform": "sko"},"message": "add sko","user": "alice@example.com"}}]`
    """
    logger.info("run entries command in batch")
    entry_commands = inject_from_ctx(EntryCommands, ctx)  # type: ignore[type-abstract]
    entry_commands.start_transaction()
    for cmd in json_arrays.load_from_file(data):
        command_type = cmd["cmdtype"]
        del cmd["cmdtype"]
        if "id" in cmd and command_type != "add_entry":
            cmd["_id"] = cmd["id"]
            del cmd["id"]
        if command_type == "add_entry":
            entry_commands.add_entry(**cmd)
        elif command_type == "update_entry":
            entry_commands.update_entry(**cmd)
        elif command_type == "delete_entry":
            entry_commands.delete_entry(**cmd)
    entry_commands.commit()


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
        config = ResourceConfig.from_dict(json_arrays.jsonlib.load_from_file(config_path))
    elif resource_id_raw:
        repo = inject_from_ctx(ResourceQueries, ctx=ctx)
        if resource := repo.by_resource_id(resource_id_raw):
            config = resource.config
        else:
            typer.echo(f"Can't find resource '{resource_id_raw}'", err=True)
            raise typer.Exit(302)
    else:
        typer.echo("You must provide either '--resource_id' or '--config/-c'", err=True)
        raise typer.Exit(code=300)

    allow_additional_properties = config.additional_properties
    schema = entry_schema.create_entry_json_schema(config.fields, allow_additional_properties)

    error_code = 0

    entries: Iterable[dict] = json_arrays.load_from_file(path, use_stdin_as_default=True)
    if as_import:
        entries = (import_entry["entry"] for import_entry in entries)
    with json_arrays.sink_from_file(err_output, use_stderr_as_default=True) as error_sink, json_arrays.sink_from_file(
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


def init_app(app):
    app.add_typer(subapp, name="entries")
