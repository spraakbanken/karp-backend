import json  # noqa: D100, I001

from tabulate import tabulate
import typer

from karp.lex_core.value_objects import UniqueId  # noqa: F401
from karp.lex_core.value_objects.unique_id import UniqueIdStr  # noqa: F401
from karp.cliapp.typer_injector import inject_from_ctx
from karp.lex_infrastructure import SqlListEntryRepos, SqlReadOnlyEntryRepoRepository
from karp.resource_commands import ResourceCommands

subapp = typer.Typer()


@subapp.command()
def create(infile: typer.FileBinaryRead, ctx: typer.Context):  # noqa: ANN201, D103
    try:
        data = json.load(infile)
    except Exception as err:  # noqa: BLE001
        typer.echo(f"Error reading file '{infile.name}': {err!s}")
        raise typer.Exit(123) from err

    resource_commands = inject_from_ctx(ResourceCommands, ctx)
    name = data.pop("resource_id")
    entry_repo = resource_commands.create_entry_repository(
        name=name,
        connection_str=data.pop("connection_str", None),
        config=data,
        user="local admin",
        message="Entry repository created",
    )

    print(f"Entry repository '{name}' with id '{entry_repo.entity_id}' created.")


@subapp.command()
def list(ctx: typer.Context):  # noqa: ANN201, D103, A001
    query = inject_from_ctx(SqlListEntryRepos, ctx)  # type: ignore [misc]
    typer.echo(
        tabulate(
            [[entry_repo.name, entry_repo.entity_id] for entry_repo in query.query()],
            headers=["name", "id"],
        )
    )


@subapp.command()
def show(ctx: typer.Context, name: str):  # noqa: ANN201, D103
    repo = inject_from_ctx(SqlReadOnlyEntryRepoRepository, ctx)  # type: ignore [misc]
    if entry_repo := repo.get_by_name(name):
        typer.echo(tabulate(((key, value) for key, value in entry_repo.dict().items())))
    else:
        typer.echo("No such entry-repo")
        raise typer.Exit(2)


def init_app(app: typer.Typer) -> None:  # noqa: D103
    app.add_typer(subapp, name="entry-repo")
