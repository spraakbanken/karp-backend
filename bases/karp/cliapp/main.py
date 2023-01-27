import logging
from typing import Optional
import sys

from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session
import typer

from karp.main import bootstrap_app, modules, config
from karp.cliapp import subapps

logger = logging.getLogger(__name__)


def create_app():
    app = typer.Typer(help="Karp CLI")
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
            ctx.obj["connection"] = app_context.container.get(Connection)
            ctx.obj["session"] = Session(bind=ctx.obj["connection"])
            logger.debug("create session", extra={"session": ctx.obj["session"]})
            ctx.obj["container"] = app_context.container.create_child_injector(
                modules.request_configuration(
                    conn=ctx.obj["connection"],
                    session=ctx.obj["session"],
                )
            )

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
