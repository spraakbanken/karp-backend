import typer


subapp = typer.Typer()
print('query')

@subapp.command
def query():
    typer.echo('query')


def init_app(app: typer.Typer) -> None:
    app.add_typer(subapp, name='query')

