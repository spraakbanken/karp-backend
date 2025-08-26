import logging
from pathlib import Path
from typing import Iterable, Optional

import typer

from karp.cliapp.utility import cli_error_handler, cli_timer

logger = logging.getLogger(__name__)


subapp = typer.Typer(name="entries", help="Commands for modifying/validating entries")

# common options
resource_option = typer.Argument(help="The ID of an existing resource", show_default=False)
data_option = typer.Argument(help="A path to a JSONL data file", show_default=False)
chunked_option = typer.Option(False, help="use to avoid loading the whole file into memory")
chunk_size_option = typer.Option(1000, help="Number of entries per chunk (only if `--chunked`)")
user_option = typer.Option(None, help="Username for edit in history", show_default=False)
message_option = typer.Option(None, help="Message for edit in history", show_default=False)


@subapp.command("add")
@cli_error_handler
@cli_timer
def add_entries_to_resource(
    ctx: typer.Context,
    resource_id: str = resource_option,
    data: Path = data_option,
    chunked: bool = chunked_option,
    chunk_size: int = chunk_size_option,
    user: Optional[str] = user_option,
    message: Optional[str] = message_option,
):
    """
    Adds new entries from a JSONL file to Karp

    > Example data row

    `{"field1":"val", "field2":["val1","val2"]}`

    - assigns new IDs to each entry
    """
    import json_arrays
    from tqdm import tqdm

    from karp.cliapp.typer_injector import inject_from_ctx
    from karp.entry_commands import EntryCommands
    from karp.foundation.value_objects import unique_id

    entry_commands = inject_from_ctx(EntryCommands, ctx)
    user = user or "local admin"
    message = message or "imported through cli"
    entries = tqdm(json_arrays.load_from_file(data), desc="Adding", unit=" entries")
    entries = ((unique_id.make_unique_id(), entry) for entry in entries)
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
    resource_id: str = resource_option,
    data: Path = data_option,
    chunked: bool = chunked_option,
    chunk_size: int = chunk_size_option,
    user: Optional[str] = user_option,
    message: Optional[str] = message_option,
):
    """
    Import entries from a JSONL file with entries and metadata (id, last_modified_by, message etc.)

    > Example data row

    `{"id":"01HBRBSYPXW6H09ETH69RRFFH5","last_modified":1744801582.805294,"resource":"my_resource","entry":{"field1":"val", "field2":["val1","val2"]}}`

    - accepts version, but will not use it, have max one version of each entry in data file

    - will use `id` from entry metadata, but generate a new one if missing

    - will use `user`/`message` from entry metadata, but fall back to user/message given as CLI option
    """
    import json_arrays
    from tqdm import tqdm

    from karp.cliapp.typer_injector import inject_from_ctx
    from karp.entry_commands import EntryCommands

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


@subapp.command("export")
@cli_error_handler
@cli_timer
def export_entries(
    ctx: typer.Context,
    resource_id: str = resource_option,
    output: typer.FileBinaryWrite = typer.Option(
        ..., "--output", "-o", help="Path to the file where the export will be saved", show_default=False
    ),
    expand_plugins: bool = typer.Option(True, help="includes/exludes fields populated by plugins"),
    entry_only: bool = typer.Option(False, help="omits/includes history information about each entry"),
):
    """
    Export all entries in a resource (latest versions)

    - --expand-plugins (default) can make the export incompatible with import

    - used to get the latest versions of entries, will not include any history information

    - useful for dumping data for batch processesing (see `karp-cli entires batch --help`)
    """
    import json_arrays

    from karp.cliapp.typer_injector import inject_from_ctx
    from karp.lex.application import EntryQueries

    entry_queries = inject_from_ctx(EntryQueries, ctx=ctx)
    entries = entry_queries.all_entries(resource_id=resource_id, expand_plugins=expand_plugins)
    logger.debug(
        "exporting entries",
        extra={"resource_id": resource_id, "type(all_entries)": type(entries)},
    )

    def gen(entries):
        for entry in entries:
            entry = entry.dict()
            if entry_only:
                entry = entry["entry"]
            yield entry

    json_arrays.dump(gen(entries), output)


@subapp.command("batch")
@cli_error_handler
@cli_timer
def batch_entries(
    ctx: typer.Context,
    data: Path = data_option,
):
    """Run entry commands in batch.

    This command expects a list with dicts with the key `cmd` that is a serialized
    command that defines `cmdtype`. Available commands: `add_entry`, `update_entry`, `delete_entry`

    - Edits that lead to conflicts will be blocked

    - Use `karp-cli entries validate ...` to check the validity of your data file before running this

    > Example data row:

    `[{"cmd": {"cmdtype": "add_entry","resource_id": "resource_a","entry": {"baseform": "sko"},"message": "add sko","user": "alice@example.com"}}]`
    """
    import json_arrays

    from karp.cliapp.typer_injector import inject_from_ctx
    from karp.entry_commands import EntryCommands
    from karp.foundation.value_objects import unique_id

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
            cmd["entry_id"] = cmd.get("entry_id") or unique_id.make_unique_id()
            entry_commands.add_entry(**cmd)
        elif command_type == "update_entry":
            entry_commands.update_entry(**cmd)
        elif command_type == "delete_entry":
            entry_commands.delete_entry(**cmd)
    entry_commands.commit()


@subapp.command("validate")
@cli_error_handler
@cli_timer
def validate_entries(
    ctx: typer.Context,
    path: Optional[Path] = data_option,
    config_path: Optional[Path] = typer.Option(
        None, "--config", "-c", help="Path to a resource config (used if `--resource-id` not given)"
    ),
    resource_id_raw: Optional[str] = typer.Option(
        None, "--resource_id", help="The ID of an existing resource (used if `--config` not given)", show_default=False
    ),
    as_import: bool = typer.Option(False, "--as-import", help="Set this to validate import format, not add format"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="If set, writes to file, else stdout"),
):
    """Validate entries without adding or importing them.

    You can either read the configuration from the database by specifing `--resource_id=<RESOURCE ID>`
    or supply an external config with `--config=<PATH>`.

    By default, this command supposes that the entries are in raw mode (like `add` works),
    to use the format the `import` uses please add the `--as-import` flag.
    """
    import collections.abc

    import json_arrays
    import json_arrays.jsonlib
    from sb_json_tools import jt_val
    from tqdm import tqdm

    from karp.cliapp.typer_injector import inject_from_ctx
    from karp.lex.application import ResourceQueries
    from karp.lex.domain.value_objects import ResourceConfig, entry_schema

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
        # ignore deletes, which do not have an entry field
        entries = (
            import_entry["entry"]
            for import_entry in entries
            if not ("cmdtype" in import_entry and import_entry["cmdtype"] == "delete_entry")
        )
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
