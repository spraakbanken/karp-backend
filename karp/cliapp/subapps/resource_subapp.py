import logging  # noqa: I001
from pathlib import Path
from typing import Callable, List, Optional, TypeVar

import typer
from json_streams import jsonlib
from tabulate import tabulate

from karp.foundation.value_objects import UniqueIdStr, unique_id
from karp.lex_infrastructure import ResourceQueries
from karp.resource_commands import ResourceCommands

from karp.cliapp.utility import cli_error_handler, cli_timer
from karp.cliapp.typer_injector import inject_from_ctx
from karp.search_commands import SearchCommands

logger = logging.getLogger("karp")


subapp = typer.Typer()


T = TypeVar("T")


def choose_from(choices: List[T], choice_fmt: Callable[[T], str]) -> T:
    for i, choice in enumerate(choices):
        typer.echo(f"{i}) {choice_fmt(choice)}")
    while True:
        number = typer.prompt(f"Choose from above with (0-{len(choices)-1}):")
        return choices[int(number)]


@subapp.command()
@cli_error_handler
@cli_timer
def create(
    ctx: typer.Context,
    config: Path,
):
    resource_commands = inject_from_ctx(ResourceCommands, ctx)
    if config.is_file():
        data = jsonlib.load_from_file(config)
        try:
            resource_id = data.pop("resource_id")
        except KeyError as exc:
            raise ValueError("'resource_id' is missing") from exc
        try:
            name = data.pop("resource_name")
        except KeyError as exc:
            raise ValueError("'resource_name' is missing") from exc
        resource_commands.create_resource(
            resource_id,
            name,
            data,
            user="local admin",
        )

        print(f"Created resource '{resource_id}'")

    elif config.is_dir():
        typer.Abort("not supported yetls")


@subapp.command()
@cli_error_handler
@cli_timer
def update(
    ctx: typer.Context,
    config: Path,
    version: int = typer.Option(..., "-v", "--version"),
    message: Optional[str] = typer.Option(None, "-m", "--message"),
    user: Optional[str] = typer.Option(None, "-u", "--user"),
):
    """Update resource config."""

    config_dict = jsonlib.load_from_file(config)
    resource_id = config_dict.pop("resource_id")
    if resource_id is None:
        raise ValueError("resource_id must be present")
    resource_name = config_dict.pop("resource_name") or resource_id
    resource_commands = inject_from_ctx(ResourceCommands, ctx)
    try:
        resource_commands.update_resource(
            resource_id=resource_id,
            name=resource_name,
            version=version,
            config=config_dict,
            message=message or "config updated",
            user=user or "local admin",
        )
    except Exception as err:  # noqa: BLE001
        typer.echo(f"Error occurred: {err}", err=True)
        raise typer.Exit(400) from err
    else:
        print(f"The config of '{resource_id}' is updated.")
        print("You may need to reindex the resource,")
        print(f"run `karp-cli resource reindex {resource_id}`")


@subapp.command()
@cli_error_handler
@cli_timer
def publish(ctx: typer.Context, resource_id: str, version: int):
    resource_commands = inject_from_ctx(ResourceCommands, ctx)
    resource_commands.publish_resource(
        resource_id=resource_id,
        message=f"Publish '{resource_id}",
        user="local admin",
        version=version,
    )
    typer.echo(f"Resource '{resource_id}' is published ")


@subapp.command()
@cli_error_handler
@cli_timer
def reindex(ctx: typer.Context, resource_id: str):
    search_commands = inject_from_ctx(SearchCommands, ctx)
    search_commands.reindex_resource(resource_id=resource_id)
    typer.echo(f"Successfully reindexed all data in {resource_id}")


@subapp.command()
@cli_error_handler
@cli_timer
def reindex_all(ctx: typer.Context):
    search_commands = inject_from_ctx(SearchCommands, ctx)
    search_commands.reindex_all_resources()
    typer.echo(f"Successfully reindexed all resrouces")


@subapp.command("list")
@cli_error_handler
@cli_timer
def list_resources(
    ctx: typer.Context,
    show_published: Optional[bool] = typer.Option(True, "--show-published/--show-all"),
):
    resources = inject_from_ctx(ResourceQueries, ctx)
    if show_published:
        result = resources.get_published_resources()
    else:
        result = resources.get_all_resources()
    typer.echo(
        tabulate(
            [
                [resource.resource_id, resource.version, resource.is_published]
                for resource in result
            ],
            headers=["resource_id", "version", "published"],
        )
    )


@subapp.command()
@cli_error_handler
@cli_timer
def show(ctx: typer.Context, resource_id: str, version: Optional[int] = None):
    resources = inject_from_ctx(ResourceQueries, ctx)  # type: ignore [misc]
    resource = resources.by_resource_id_optional(resource_id, version=version)
    if not resource:
        version_str = version or "latest"
        typer.echo(f"Can't find resource '{resource_id}', version '{version_str}'", err=True)
        raise typer.Exit(3)

    typer.echo(tabulate(((key, value) for key, value in resource.dict().items())))


@subapp.command()
@cli_error_handler
@cli_timer
def delete(
    ctx: typer.Context,
    resource_id: str,
    user: Optional[str] = typer.Option(None),
    message: Optional[str] = typer.Option(None),
):
    resource_commands = inject_from_ctx(ResourceCommands, ctx)
    resource_commands.delete_resource(
        resource_id=resource_id,
        user=user or "local admin",
        message=message or "resource deleted",
    )
    typer.echo(f"Deleted resource '{resource_id}'")


def init_app(app):
    app.add_typer(subapp, name="resource")
