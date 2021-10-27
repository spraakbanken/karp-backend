from tabulate import tabulate
import typer

from karp.lex.application.queries import ListEntryRepos
from .typer_injector import inject_from_ctx


subapp = typer.Typer()


@subapp.command()
def create():
    pass


@subapp.command()
def list(ctx: typer.Context):
    query = inject_from_ctx(ListEntryRepos, ctx)
    typer.echo(
        tabulate(
            [
                [entry_repo.name, entry_repo.id]
                for entry_repo in query.query()
            ],
            headers=['name', 'id']
        )
    )


def init_app(app: typer.Typer) -> None:
    app.add_typer(subapp, name='entry-repo')
