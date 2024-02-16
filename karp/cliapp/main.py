import logging  # noqa: I001
from typing import Optional
import sys

from sqlalchemy.orm import Session
import typer

from karp.main import bootstrap_app, modules, config
from karp.cliapp import subapps

logger = logging.getLogger(__name__)


def create_app():
    app = typer.Typer(help="Karp CLI", rich_markup_mode="markdown")
    app_context = bootstrap_app()

    @app.callback()
    def set_app_context(
        ctx: typer.Context,
        version: Optional[bool] = typer.Option(
            None, "--version", callback=version_callback, is_eager=True
        ),
    ):
        if ctx.invoked_subcommand is None:
            ctx.obj = {}
        else:
            ctx.obj = {}
            # This leaks the session object but it's only 1 so never mind
            ctx.obj["container"] = modules.with_new_session(app_context.container)

    subapps.add_subapps(app)
    load_commands(app)

    return app


def version_callback(value: bool):
    if value:
        typer.echo(f"{config.PROJECT_NAME} CLI {config.VERSION}")
        raise typer.Exit()


def load_commands(app: typer.Typer):
    modules.load_modules("karp.clicommands", app=app)


cliapp = create_app()


if __name__ == "__main__":
    # cliapp = create_app()
    cliapp()
