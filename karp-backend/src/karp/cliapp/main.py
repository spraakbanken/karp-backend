import logging  # noqa: D100, I001
from typing import Optional
import sys  # noqa: F401

from sqlalchemy.orm import Session
import typer

from karp.main import bootstrap_app, modules, config
from karp.cliapp import subapps

logger = logging.getLogger(__name__)


def create_app():  # noqa: ANN201, D103
    app = typer.Typer(help="Karp CLI", rich_markup_mode="markdown")
    app_context = bootstrap_app()

    @app.callback()
    def set_app_context(  # noqa: ANN202
        ctx: typer.Context,
        version: Optional[bool] = typer.Option(
            None, "--version", callback=version_callback, is_eager=True
        ),
    ):
        if ctx.invoked_subcommand is None:
            ctx.obj = {}
        else:
            ctx.obj = {}
            ctx.obj["container"] = app_context.container

    subapps.add_subapps(app)
    load_commands(app)

    return app


def version_callback(value: bool):  # noqa: ANN201, D103
    if value:
        typer.echo(f"{config.PROJECT_NAME} CLI {config.VERSION}")
        raise typer.Exit()


def load_commands(app: typer.Typer):  # noqa: ANN201, D103
    modules.load_modules("karp.clicommands", app=app)


cliapp = create_app()


if __name__ == "__main__":
    # cliapp = create_app()
    cliapp()
