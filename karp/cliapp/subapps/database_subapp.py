import typer

from karp.main.migrations.use_cases import run_migrations_down, run_migrations_up

subapp = typer.Typer()


@subapp.command(name="up")
def migrations_up(  # noqa: ANN201, D103
    ctx: typer.Context,
):
    run_migrations_up()


@subapp.command(name="down")
def migrations_down(  # noqa: ANN201, D103
    ctx: typer.Context,
):
    run_migrations_down()


def init_app(app: typer.Typer) -> None:  # noqa: D103
    app.add_typer(subapp, name="db")
