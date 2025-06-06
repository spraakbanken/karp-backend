from pathlib import Path
from typing import Callable, List, Optional, TypeVar

import typer
from typer.core import TyperGroup

from karp.cliapp.utility import cli_error_handler, cli_timer


class OrderCommands(TyperGroup):
    """This class makes the help page show the commands in the order they are defined"""

    def list_commands(self, *_):
        return list(self.commands)


subapp = typer.Typer(cls=OrderCommands, name="resource", help="Commands for creating, updating or removing resources")


T = TypeVar("T")


def choose_from(choices: List[T], choice_fmt: Callable[[T], str]) -> T:
    for i, choice in enumerate(choices):
        typer.echo(f"{i}) {choice_fmt(choice)}")
    while True:
        number = typer.prompt(f"Choose from above with (0-{len(choices)-1}):")
        return choices[int(number)]


config_option = typer.Argument(help="A path to a resource config file", show_default=False)
resource_option = typer.Argument(help="The ID of an existing resource", show_default=False)
version_option = typer.Argument(None, help="The version to do this operation on")
remove_old_index_option = typer.Option(False, help="If set, will remove the old index when the new one is completed.")


@subapp.command()
@cli_error_handler
@cli_timer
def create(
    ctx: typer.Context,
    config_path: Path = config_option,
):
    """
    Create a new resource from a configuration file

    - create does not publish a resource
    """
    from karp.cliapp.typer_injector import inject_from_ctx
    from karp.lex.domain.value_objects import ResourceConfig
    from karp.resource_commands import ResourceCommands

    resource_commands = inject_from_ctx(ResourceCommands, ctx)

    if config_path.is_dir():
        typer.Abort("Config needs to be a JSON or YAML file")

    elif config_path.exists():
        config = ResourceConfig.from_path(config_path)
        resource_commands.create_resource(config, user="local admin")
        print(f"Created resource '{config.resource_id}'")

    else:
        typer.echo(f"The config file {config_path} was not found.", err=True)
        typer.echo("Could not create the resource.", err=True)
        raise typer.Exit(1)


@subapp.command()
@cli_error_handler
@cli_timer
def update(
    ctx: typer.Context,
    config: Path = config_option,
    version: Optional[int] = typer.Option(None, "-v", "--version"),
    message: Optional[str] = typer.Option(None, "-m", "--message"),
    user: Optional[str] = typer.Option(None, "-u", "--user"),
):
    """Update an existing resource

    - this changes the configuration and will affect future edits, but it does not check that the current
    entries in resource are valid with the new configration.

    - for some changes, `karp-cli resource reindex <resource_id>` is needed
    """

    from karp.cliapp.typer_injector import inject_from_ctx
    from karp.lex.domain.value_objects import ResourceConfig
    from karp.resource_commands import ResourceCommands

    config = ResourceConfig.from_path(config)
    resource_id = config.resource_id
    resource_commands = inject_from_ctx(ResourceCommands, ctx)
    try:
        resource_commands.update_resource(
            resource_id=resource_id,
            version=version,
            config=config,
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
def publish(ctx: typer.Context, resource_id: str = resource_option, version: Optional[int] = version_option):
    """
    Publish a resource

    Makes the resource available from search and edit.
    """
    from karp.cliapp.typer_injector import inject_from_ctx
    from karp.resource_commands import ResourceCommands

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
def reindex(
    ctx: typer.Context,
    resource_id: str = resource_option,
    remove_old_index: Optional[bool] = remove_old_index_option,
):
    """
    Recreate the search index for a resource

    - Needed for some changes in the configuration and if the data is outdated (edits made when Elasticsearch was down)

    - Deletes the old index after reindexing.

    - Edits made during reindex may be lost (from index, not Karp)
    """
    from karp.cliapp.typer_injector import inject_from_ctx
    from karp.search_commands import SearchCommands

    search_commands = inject_from_ctx(SearchCommands, ctx)
    search_commands.reindex_resource(resource_id=resource_id, remove_old_index=remove_old_index)
    typer.echo(f"Successfully reindexed all data in {resource_id}")


@subapp.command()
@cli_error_handler
@cli_timer
def reindex_all(ctx: typer.Context, remove_old_index: Optional[bool] = remove_old_index_option):
    """
    Reindexes all resources in Karp, see `karp-cli resource reindex -help` for more details
    """
    from karp.cliapp.typer_injector import inject_from_ctx
    from karp.search_commands import SearchCommands

    search_commands = inject_from_ctx(SearchCommands, ctx)
    search_commands.reindex_all_resources(remove_old_index=remove_old_index)
    typer.echo("Successfully reindexed all resrouces")


@subapp.command("list")
@cli_error_handler
@cli_timer
def list_resources(
    ctx: typer.Context,
    show_published: Optional[bool] = typer.Option(
        True, "--show-published/--show-all", help="Either show only published or all resources"
    ),
):
    """
    Lists (latest version of) resources, by default only published ones
    """
    from tabulate import tabulate

    from karp.cliapp.typer_injector import inject_from_ctx
    from karp.lex.application import ResourceQueries

    resources = inject_from_ctx(ResourceQueries, ctx)
    if show_published:
        result = resources.get_published_resources()
    else:
        result = resources.get_all_resources()
    typer.echo(
        tabulate(
            [[resource.resource_id, resource.version, resource.is_published] for resource in result],
            headers=["resource_id", "version", "published"],
        )
    )


@subapp.command()
@cli_error_handler
@cli_timer
def show(ctx: typer.Context, resource_id: str = resource_option, version: Optional[int] = version_option):
    """
    Show metadata and config for a resource, supports showing old versions

    Useful for checking what the config is and how it has changed.
    """
    from tabulate import tabulate

    from karp.cliapp.typer_injector import inject_from_ctx
    from karp.lex.application import ResourceQueries

    resources = inject_from_ctx(ResourceQueries, ctx)  # type: ignore [misc]
    resource = resources.by_resource_id(resource_id, version=version)
    typer.echo(tabulate(((key, value) for key, value in resource.dict().items() if key != "config")))
    typer.echo()
    typer.echo(resource.config.config_str)


@subapp.command()
@cli_error_handler
@cli_timer
def unpublish(
    ctx: typer.Context,
    resource_id: str,
    version: Optional[int] = None,
    keep_index: bool = False,
):
    """
    Unpublish resource

    Makes the resources unavailable for search and editing. By default the search index
    is removed.
    """
    from karp.cliapp.typer_injector import inject_from_ctx
    from karp.resource_commands import ResourceCommands

    resource_commands = inject_from_ctx(ResourceCommands, ctx)
    unpublished = resource_commands.unpublish_resource(
        resource_id=resource_id, user="local admin", version=version, keep_index=keep_index
    )
    if unpublished:
        typer.echo("Resource unpublished")
        if keep_index:
            typer.echo("Elasticsearch index kept")
    else:
        typer.echo("Resource already unpublished")


@subapp.command()
@cli_error_handler
@cli_timer
def delete(
    ctx: typer.Context,
    resource_id: str = resource_option,
    force: Optional[bool] = typer.Option(False, help="To prompt the user before removal or not"),
):
    """
    Completely delete resource, nothing will be saved
    """
    from karp.cliapp.typer_injector import inject_from_ctx
    from karp.resource_commands import ResourceCommands

    resource_commands = inject_from_ctx(ResourceCommands, ctx)
    if not force:
        force = typer.confirm(
            "This will delete every row, table and index for this resource permanently. Are you sure?"
        )
    if force:
        deleted = resource_commands.delete_resource(resource_id=resource_id)
        if deleted:
            typer.echo("Resource deleted")
        else:
            typer.echo("Resource already deleted")
    else:
        typer.echo("Resource not deleted")
