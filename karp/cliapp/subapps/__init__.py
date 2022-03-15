import typer

from karp.cliapp.subapps import query_subapp


def add_subapps(app: typer.Typer) -> None:
    query_subapp.init_app(app)
