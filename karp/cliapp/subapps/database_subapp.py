import typer

from karp.main.migrations.use_cases import run_migrations_down, run_migrations_up

subapp = typer.Typer(name="db", help="Initialize or upgrade database using `karp-cli db up`")


@subapp.command(name="up")
def migrations_up(
    ctx: typer.Context,
):
    """
    Initalizes the database with the needed tables or upgrades existing tables.

    It is generally safe to run this command any time, if the database is already
    upd to date, the command will do nothing.
    """
    run_migrations_up()


@subapp.command(name="down")
def migrations_down(
    ctx: typer.Context,
):
    "Downgrades the database to a previous version. WARNING: untested"
    run_migrations_down()
