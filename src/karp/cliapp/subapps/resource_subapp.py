import subprocess
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
        number = typer.prompt(f"Choose from above with (0-{len(choices) - 1}):")
        return choices[int(number)]


config_option = typer.Argument(help="A path to a resource config file", show_default=False)
resource_option = typer.Argument(help="The ID of an existing resource", show_default=False)
version_option = typer.Argument(None, help="The version to do this operation on")
remove_old_index_option = typer.Option(False, help="If set, will remove the old index when the new one is completed.")


def _reload_backend():
    p = subprocess.run(["make", "reload"], capture_output=True)
    if p.returncode != 0:
        typer.echo("Failed to reload backend.")
    else:
        typer.echo("Backend reloaded.")


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
    from karp import resource_commands
    from karp.lex.domain.value_objects import ResourceConfig

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

    from karp import resource_commands
    from karp.lex.domain.value_objects import ResourceConfig

    config = ResourceConfig.from_path(config)
    resource_id = config.resource_id
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

    If a resource is published, the CLI tries to reload a running instance of backend to clear caches.
    """
    from karp import resource_commands

    resource_commands.publish_resource(
        resource_id=resource_id,
        message=f"Publish '{resource_id}",
        user="local admin",
        version=version,
    )
    typer.echo(f"Resource '{resource_id}' is published ")
    _reload_backend()


@subapp.command()
@cli_error_handler
@cli_timer
def reindex(
    ctx: typer.Context, resource_id: str = resource_option, remove_old_index: Optional[bool] = remove_old_index_option
):
    """
    Recreate the search index for a resource

    - Needed for some changes in the configuration and if the data is outdated (edits made when Elasticsearch was down)

    - If remove-old-index, deletes the old index after reindexing, default is to keep the old index (--no-remove-old-index)

    - Will first fetch all entries and reindex. Then fetch entries that are edited since last fetch. Do this in a loop until no new changes are seen.
      There is a very small risk that something will be edited in the short time during which the index alias is being pointed to new new index.
    """
    from karp import search_commands

    count, gen = search_commands.reindex_resource(resource_id=resource_id, remove_old_index=remove_old_index)

    # a progress bar that renders poorly, but better than nothing
    with typer.progressbar(length=count, label="Indexing progress", show_eta=False) as progress:
        for i, _ in enumerate(gen):
            progress.update(1)
            progress.label = f"Indexing progress ({i} / {count})"
    typer.echo(f"Successfully reindexed all data in {resource_id}")

    # reload backend to make sure that backend sees changes to index
    _reload_backend()


@subapp.command()
@cli_error_handler
def set_index(
    ctx: typer.Context,
    resource_id: str = resource_option,
    index: str = typer.Argument(help="The name of an existing OpenSearch index"),
):
    from karp import search_commands

    """
    Sets an existing OpenSearch index as the current index for the given resource.
    """
    search_commands.set_index(resource_id, index)


@subapp.command()
@cli_error_handler
@cli_timer
def reindex_all(ctx: typer.Context, remove_old_index: Optional[bool] = remove_old_index_option):
    """
    Reindexes all resources in Karp, see `karp-cli resource reindex --help` for more details
    """
    from karp import search_commands

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
    show_current_index: Optional[bool] = typer.Option(
        True, "--show-current-index/--show-all-indices", help="Shows current or all indices associated with resource."
    ),
    resource_filter: list[str] = typer.Argument(
        default_factory=list,
        metavar="RESOURCE_ID",
        help="Filter by given resource ids. If omitted, show all resources.  Supports glob pattern * for zero or more of any character and ? for any character once.",
    ),
):
    """
    Lists (latest version of) resources, by default only published ones. Current index or all indices associated with
    the resource are listed, along with index size.

    Filter by resource id, by giving the wanted resource ids as arguments.
    """

    from karp.cliapp.utility import tabulate
    from karp.lex.infrastructure.sql import resource_repository
    from karp.search.infrastructure.opensearch.indices import get_indices_data

    warnings = []
    headers = ["resource_id", "version"]

    if show_published:
        result = resource_repository.get_published_resources()
    else:
        # only show published column when showing all
        headers.append("published")
        result = resource_repository.get_all_resources()

    headers.append("index")
    headers.append("size")

    resource_id_to_indices = get_indices_data(
        (resource.resource_id for resource in result), only_aliased=show_current_index
    )

    resource_matcher = _get_resource_id_matcher(resource_filter)

    rows = []
    for resource in result:
        if not resource_matcher(resource.resource_id):
            continue

        row = [resource.resource_id, resource.version]
        if not show_published:
            # only show published column when showing all
            row.append("published" if resource.is_published else "unpublished")
        if show_current_index:
            active_index = resource_id_to_indices.get(resource.resource_id)[0]
            row.append(active_index.name)
            row.append(active_index.size)
            rows.append(row)
        else:
            # adds one row to tabulation for each index
            orig_row_len = len(row)
            indices = resource_id_to_indices.get(resource.resource_id)
            for index in indices:
                if index.current:
                    row.append(f"{index.name} (current)")
                else:
                    row.append(index.name)
                row.append(index.size)
                rows.append(row)

                row = [""] * orig_row_len

    typer.echo(
        tabulate(
            rows,
            headers=headers,
        )
    )
    for warning in warnings:
        typer.echo(f"WARNING: {warning}")


@subapp.command()
@cli_error_handler
@cli_timer
def show(ctx: typer.Context, resource_id: str = resource_option, version: Optional[int] = version_option):
    """
    Show metadata and config for a resource, supports showing old versions

    Useful for checking what the config is and how it has changed.
    """

    from karp.cliapp.utility import tabulate
    from karp.lex.application import resource_queries

    resource = resource_queries.by_resource_id(resource_id, version=version)

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
    from karp import resource_commands

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
    from karp import resource_commands

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


def _get_resource_id_matcher(resource_filter: list[str]):
    """
    Create regexps from the glob filters (resource_filter) and return a function
    that returns True if any of the filters match. If there are no filters, always
    return True.
    """
    import re

    res = []
    for elem in resource_filter:
        filter_re = "^" + elem.replace("*", ".*").replace("?", ".") + "$"
        res.append(filter_re)

    def resource_matcher(resource_id: str) -> bool:
        if res:
            for filter_re in res:
                if re.match(filter_re, resource_id) is not None:
                    return True
            return False
        return True

    return resource_matcher
