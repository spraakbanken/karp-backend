import typer

from karp.main.migrations.use_cases import run_migrations_down, run_migrations_up

subapp = typer.Typer()


@subapp.command(name="up")
def migrations_up(
    ctx: typer.Context,
):
    run_migrations_up()


@subapp.command(name="down")
def migrations_down(
    ctx: typer.Context,
):
    run_migrations_down()


def init_app(app: typer.Typer) -> None:
    app.add_typer(subapp, name="db")
