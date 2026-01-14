import sys
from pathlib import Path
from typing import Annotated

import typer

from karp.cliapp import subapps

app = typer.Typer(help="Karp CLI", rich_markup_mode="markdown", pretty_exceptions_enable=False)


def create_app():
    @app.callback()
    def set_app_context(
        ctx: typer.Context,
        version: bool | None = typer.Option(None, "--version", callback=version_callback, is_eager=True),
    ):
        if "--help" in sys.argv and "repl" not in sys.argv:
            return

        from karp.main import bootstrap_app

        bootstrap_app()

        from karp.globals import new_session

        ctx.with_resource(new_session())

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
    script: Path | None = typer.Argument(
        None,
        help="optional script file to run instead of entering REPL",
    ),
    args: list[str] = typer.Argument(None, help="list of args to pass to script file"),
):
    """Start a Python REPL with the Karp API available."""
    import code
    import readline
    import rlcompleter

    from karp.entry_commands import EntryCommands
    from karp.globals import _engine_ctx_var
    from karp.search.domain import QueryRequest
    from karp.search.infrastructure.es.search_service import EsSearchService

    if not args:
        args = []

    locals = {  # noqa: A001
        "ctx": ctx,
        "engine": _engine_ctx_var.get(),
        "entry_commands": EntryCommands(),
        "es_search_service": EsSearchService(),
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
