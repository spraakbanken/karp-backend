import typer

from karp.cliapp.subapps.auth_subapp import subapp as auth_subapp
from karp.cliapp.subapps.database_subapp import subapp as database_subapp
from karp.cliapp.subapps.entries_subapp import subapp as entries_subapp
from karp.cliapp.subapps.resource_subapp import subapp as resource_subapp


def add_subapps(app: typer.Typer) -> None:
    app.add_typer(auth_subapp)
    app.add_typer(database_subapp)
    app.add_typer(entries_subapp)
    app.add_typer(resource_subapp)
