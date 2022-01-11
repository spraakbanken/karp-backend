import json

from tabulate import tabulate
import typer

from karp.foundation.commands import CommandBus
from karp.lex.application.queries import ListEntryRepos
from karp.lex.domain.commands import CreateEntryRepository
from .typer_injector import inject_from_ctx


subapp = typer.Typer()


@subapp.command()
def create(infile: typer.FileBinaryRead, ctx: typer.Context):
    data = json.load(infile)
    create_entry_repo = CreateEntryRepository.from_dict(
        data,
        user='local admin',
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
def list(ctx: typer.Context):
    query = inject_from_ctx(ListEntryRepos, ctx)
    typer.echo(
        tabulate(
            [

                [entry_repo.name, entry_repo.id, entry_repo.repository_type]
                for entry_repo in query.query()
            ],
            headers=['name', 'id', 'repository_type']
        )
    )


def init_app(app: typer.Typer) -> None:
    app.add_typer(subapp, name='entry-repo')
