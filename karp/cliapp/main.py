import sys
from pathlib import Path
from typing import Annotated, Optional

import typer

from karp.cliapp import subapps

app = typer.Typer(help="Karp CLI", rich_markup_mode="markdown", pretty_exceptions_enable=False)


def create_app():
    @app.callback()
    def set_app_context(
        ctx: typer.Context,
        version: Optional[bool] = typer.Option(None, "--version", callback=version_callback, is_eager=True),
    ):
        if "--help" in sys.argv and "repl" not in sys.argv:
            return
        from karp.main import bootstrap_app, with_new_session

        app_context = bootstrap_app()
        if ctx.invoked_subcommand is None:
            ctx.obj = {}
        else:
            ctx.obj = {}
            # This leaks the session object but it's only 1 so never mind
            ctx.obj["injector"] = with_new_session(app_context.injector)

    subapps.add_subapps(app)

    return app


def version_callback(value: bool):
    if value:
        from karp.main import config

        typer.echo(f"{config.PROJECT_NAME} CLI {config.VERSION}")
        raise typer.Exit()


@app.command("repl")
def repl(
    ctx: typer.Context,
    interactive: Annotated[
        bool,
        typer.Option(
            "--interactive",
            "-i",
            help="enter a REPL after running the script",
        ),
    ] = False,
    script: Optional[Path] = typer.Argument(
        None,
        help="optional script file to run instead of entering REPL",
    ),
    args: list[str] = typer.Argument(None, help="list of args to pass to script file"),
):
    """Start a Python REPL with the Karp API available."""
    import code
    import readline
    import rlcompleter

    from sqlalchemy.engine import Engine
    from sqlalchemy.orm import Session

    from karp.auth.infrastructure.api_key_service import APIKeyService
    from karp.cliapp.typer_injector import inject_from_ctx
    from karp.entry_commands import EntryCommands
    from karp.lex.application import EntryQueries, ResourceQueries, SearchQueries
    from karp.lex.infrastructure import ResourceRepository
    from karp.resource_commands import ResourceCommands
    from karp.search.domain import QueryRequest
    from karp.search.infrastructure import EsSearchService
    from karp.search_commands import SearchCommands

    if not args:
        args = []

    locals = {  # noqa: A001
        "ctx": ctx,
        "injector": ctx.obj["injector"],
        "engine": inject_from_ctx(Engine, ctx),
        "session": inject_from_ctx(Session, ctx),
        "resource_queries": inject_from_ctx(ResourceQueries, ctx),
        "entry_queries": inject_from_ctx(EntryQueries, ctx),
        "search_queries": inject_from_ctx(SearchQueries, ctx),
        "resource_commands": inject_from_ctx(ResourceCommands, ctx),
        "entry_commands": inject_from_ctx(EntryCommands, ctx),
        "search_commands": inject_from_ctx(SearchCommands, ctx),
        "resources": inject_from_ctx(ResourceRepository, ctx),
        "es_search_service": inject_from_ctx(EsSearchService, ctx),
        "api_key_service": inject_from_ctx(APIKeyService, ctx),
        "QueryRequest": QueryRequest,
    }

    module = sys.__class__
    karp_api = module("karp_api")
    karp_api.__dict__.update(locals)
    sys.modules["karp_api"] = karp_api

    banner = ["The following objects are available:"]
    for name, obj in locals.items():
        cls = type(obj).__name__
        mod = type(obj).__module__
        if mod.startswith("karp."):
            banner.append(f"  {name}: {cls} ({mod})")
        else:
            banner.append(f"  {name}: {cls}")
    banner = "\n".join(banner)

    exitmsg = "Leaving the Karp REPL."

    if "libedit" in readline.__doc__:
        readline.parse_and_bind("bind ^I complete")
    else:
        readline.parse_and_bind("tab: complete")
    readline.set_completer(rlcompleter.Completer(locals).complete)

    sys.path.insert(0, "")
    console = code.InteractiveConsole(locals)
    if script is not None:
        locals["__file__"] = str(script)
        path = script.absolute().parent
        sys.path.insert(0, str(path))
        sys.argv = [str(script)] + args
        with open(script) as file:
            console.runsource(file.read(), filename=str(script), symbol="exec")

    if script is None or interactive:
        console.interact(banner, exitmsg)


cliapp = create_app()


if __name__ == "__main__":
    cliapp()
