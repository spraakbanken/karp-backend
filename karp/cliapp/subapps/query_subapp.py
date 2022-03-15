import typer

from karp import search
from karp.cliapp.typer_injector import inject_from_ctx


subapp = typer.Typer()


@subapp.command()
def resource(
    resource_id: str,
    ctx: typer.Context,
):
    typer.echo('query')
    search_service = inject_from_ctx(search.SearchService, ctx)
    query_request = search.QueryRequest(resource_ids=[resource_id])
    typer.echo(search_service.query(query_request))


def init_app(app: typer.Typer) -> None:
    app.add_typer(subapp, name='query')
