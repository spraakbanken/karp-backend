import typer

from karp.cliapp.subapps import (
    auth_subapp,
    database_subapp,
    entries_subapp,
    query_subapp,
    resource_subapp,
)


def add_subapps(app: typer.Typer) -> None:
    auth_subapp.init_app(app)
    database_subapp.init_app(app)
    entries_subapp.init_app(app)
    query_subapp.init_app(app)
    resource_subapp.init_app(app)
