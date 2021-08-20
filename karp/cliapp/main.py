import logging
from typing import Optional

try:
    from importlib.metadata import entry_points
except ImportError:
    from importlib_metadata import entry_points  # type: ignore

import typer

from . import app_config

logger = logging.getLogger("karp")

__version__ = "0.8.1"


def create_app():
    app = typer.Typer(help="Karp CLI")

    @app.command()
    def main(
        version: Optional[bool] = typer.Option(
            None, "--version", callback=version_callback, is_eager=True
        )
    ):
        pass

    # from karp.application.services.contexts import init_context

    # init_context()

    load_commands(app)

    return app


def version_callback(value: bool):
    if value:
        typer.echo(f"Karp CLI version: {__version__}")
        raise typer.Exit()


def load_commands(app=None):
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
