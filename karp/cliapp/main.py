import logging
from typing import Optional

try:
    from importlib.metadata import entry_points
except ImportError:
    from importlib_metadata import entry_points  # type: ignore

import typer

from karp.main import bootstrap_app

logger = logging.getLogger("karp")

__version__ = "6.0.0"


def create_app():
    app = typer.Typer(help="Karp CLI")

    @app.callback()
    def set_app_context(
        ctx: typer.Context,
        version: Optional[bool] = typer.Option(
            None, "--version", callback=version_callback, is_eager=True
        )
    ):
        if ctx.invoked_subcommand is None:
            typer.echo("empty")
        else:
            typer.echo("setting app_context")
            ctx.obj = {}
            ctx.obj['app_context'] = bootstrap_app()

    load_commands(app)

    return app


def version_callback(value: bool):
    if value:
        typer.echo(f"Karp CLI version: {__version__}")
        raise typer.Exit()


def load_commands(app=None):
    if "karp.clicommands" not in entry_points():
        return

    for ep in entry_points()["karp.clicommands"]:
        logger.info("Loading cli module: %s", ep.name)
        print("Loading cli module: %s" % ep.name)
        mod = ep.load()
        if app:
            init_app = getattr(mod, "init_app", None)
            if init_app:
                init_app(app)


cliapp = create_app()

if __name__ == "__main__":
    # cliapp = create_app()
    cliapp()
