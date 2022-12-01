import typer

from karp.main.migrations import use_cases as migration_usecases


subapp = typer.Typer()


@subapp.command(name="up")
def migrations_up(
    ctx: typer.Context,
):
    uc = migration_usecases.RunningMigrationsUp()
    uc.execute(migration_usecases.RunMigrationsUp())


@subapp.command(name="down")
def migrations_down(
    ctx: typer.Context,
):
    uc = migration_usecases.RunningMigrationsDown()
    uc.execute(migration_usecases.RunMigrationsDown())


def init_app(app: typer.Typer) -> None:
    app.add_typer(subapp, name="db")
