import json
from typing import Optional

from tabulate import tabulate
import typer

from karp import lex
from karp.foundation.value_objects import UniqueId
from karp.foundation.commands import CommandBus
from karp.foundation.value_objects.unique_id import UniqueIdStr
from karp.lex.application.queries import ListEntryRepos
from karp.lex.domain.commands import CreateEntryRepository
from karp.cliapp.typer_injector import inject_from_ctx


subapp = typer.Typer()


@subapp.command()
def create(infile: typer.FileBinaryRead, ctx: typer.Context):
    try:
        data = json.load(infile)
    except Exception as err:
        typer.echo(f"Error reading file '{infile.name}': {str(err)}")
        raise typer.Exit(123)
    create_entry_repo = CreateEntryRepository.from_dict(
        data,
        user="local admin",
    )

    bus = inject_from_ctx(CommandBus, ctx)

    bus.dispatch(create_entry_repo)

    typer.echo(
        "Entry repository '{name}' with id '{id}' created.".format(
            name=create_entry_repo.name,
            id=create_entry_repo.entity_id,
        )
    )


@subapp.command()
def delete(
    entity_id: str,  # TODO: use UniqueIdStr when supported,
    ctx: typer.Context,
    user: Optional[str] = typer.Option(None),
):

    # bus = inject_from_ctx(CommandBus, ctx)

    # delete_entry_repo = DeleteEntryRepo(
    #     entity_id=entity_id,
    #     user=user or "local admin"
    # )
    # typer.echo(f"Entry repository with id '{entity_id}' deleted.")
    typer.echo("not yet supported")


@subapp.command()
def list(ctx: typer.Context):
    query = inject_from_ctx(ListEntryRepos, ctx)
    typer.echo(
        tabulate(
            [
                [entry_repo.name, entry_repo.entity_id, entry_repo.repository_type]
                for entry_repo in query.query()
            ],
            headers=["name", "id", "repository_type"],
        )
    )


@subapp.command()
def show(ctx: typer.Context, name: str):
    repo = inject_from_ctx(lex.ReadOnlyEntryRepoRepositry, ctx)
    entry_repo = repo.get_by_name(name)
    if entry_repo:
        typer.echo(tabulate(((key, value) for key, value in entry_repo.dict().items())))
    else:
        typer.echo("No such entry-repo")
        raise typer.Exit(2)


def init_app(app: typer.Typer) -> None:
    app.add_typer(subapp, name="entry-repo")
