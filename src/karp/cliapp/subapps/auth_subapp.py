from typing import List

import typer

from karp.foundation.value_objects import PermissionLevel

subapp = typer.Typer(name="auth", help="Show, add or remove API keys", deprecated=True)


def do_imports():
    from karp.auth.infrastructure.api_key_service import APIKeyService
    from karp.cliapp.typer_injector import inject_from_ctx

    return APIKeyService, inject_from_ctx


@subapp.command(help="Create a new API key")
def create_api_key(
    ctx: typer.Context,
    resources: List[str],
    username: str,
    level: PermissionLevel,
):
    APIKeyService, inject_from_ctx = do_imports()
    api_key_service = inject_from_ctx(APIKeyService, ctx)
    key = api_key_service.create_api_key(username, resources, level)
    typer.echo(key)


@subapp.command(help="Deletes an API key")
def delete_api_key(ctx: typer.Context, api_key: str):
    APIKeyService, inject_from_ctx = do_imports()
    api_key_service = inject_from_ctx(APIKeyService, ctx)
    api_key_service.delete_api_key(api_key)


@subapp.command(help="Lists the current an API keys")
def list_api_keys(
    ctx: typer.Context,
):
    from tabulate import tabulate

    APIKeyService, inject_from_ctx = do_imports()

    api_key_service = inject_from_ctx(APIKeyService, ctx)
    result = api_key_service.list_keys()
    typer.echo(
        tabulate(
            [[api_key["api_key"], api_key["username"], api_key["permissions"]] for api_key in result],
            headers=["API key", "Username", "Permission object"],
        )
    )
