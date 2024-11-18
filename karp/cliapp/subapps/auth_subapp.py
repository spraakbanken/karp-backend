from typing import List

import typer
from tabulate import tabulate

from karp.auth.infrastructure import APIKeyService
from karp.cliapp.typer_injector import inject_from_ctx
from karp.foundation.value_objects import PermissionLevel

subapp = typer.Typer()


@subapp.command()
def create_api_key(
    ctx: typer.Context,
    resources: List[str],
    username: str,
    level: PermissionLevel,
):
    api_key_service = inject_from_ctx(APIKeyService, ctx)
    key = api_key_service.create_api_key(username, resources, level)
    typer.echo(key)


@subapp.command()
def delete_api_key(ctx: typer.Context, api_key: str):
    api_key_service = inject_from_ctx(APIKeyService, ctx)
    api_key_service.delete_api_key(api_key)


@subapp.command()
def list_api_keys(
    ctx: typer.Context,
):
    api_key_service = inject_from_ctx(APIKeyService, ctx)
    result = api_key_service.list_keys()
    typer.echo(
        tabulate(
            [[api_key["api_key"], api_key["username"], api_key["permissions"]] for api_key in result],
            headers=["API key", "Username", "Permission object"],
        )
    )


def init_app(app: typer.Typer) -> None:
    app.add_typer(subapp, name="auth")
