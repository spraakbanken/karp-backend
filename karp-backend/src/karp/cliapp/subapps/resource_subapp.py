import logging  # noqa: D100, I001
from pathlib import Path
from typing import Callable, List, Optional, TypeVar

import typer
from json_streams import jsonlib
from tabulate import tabulate

from karp import lex
from karp.command_bus import CommandBus
from karp.lex_core.value_objects import UniqueIdStr, unique_id
from karp.lex_core import commands as lex_commands
from karp.search import commands as search_commands
from karp.lex.application.queries import (
    GetPublishedResources,
    ListEntryRepos,
    GetResources,
)
from karp.main.errors import ResourceAlreadyPublished

from karp.cliapp.utility import cli_error_handler, cli_timer
from karp.cliapp.typer_injector import inject_from_ctx


logger = logging.getLogger("karp")


subapp = typer.Typer()


T = TypeVar("T")


def choose_from(choices: List[T], choice_fmt: Callable[[T], str]) -> T:  # noqa: D103
    for i, choice in enumerate(choices):
        typer.echo(f"{i}) {choice_fmt(choice)}")
    while True:
        number = typer.prompt(f"Choose from above with (0-{len(choices)-1}):")
        return choices[int(number)]


@subapp.command()
@cli_error_handler
@cli_timer
def create(  # noqa: ANN201, D103
    ctx: typer.Context,
    config: Path,
    entry_repo_id: Optional[str] = typer.Option(None, help="id for entry-repo"),
):
    bus = inject_from_ctx(CommandBus, ctx)  # type: ignore [misc]
    if config.is_file():
        data = jsonlib.load_from_file(config)
        if not entry_repo_id:
            query = inject_from_ctx(ListEntryRepos, ctx)  # type: ignore [misc]
            entry_repos = list(query.query())
            entry_repo = choose_from(
                entry_repos, lambda x: f"{x.name} {x.repository_type}"
            )
            entry_repo_uuid = entry_repo.entity_id
        else:
            entry_repo_uuid = UniqueIdStr.validate(entry_repo_id)
        cmd = lex_commands.CreateResource.from_dict(
            data,
            user="local admin",
            entry_repo_id=entry_repo_uuid,
        )
        bus.dispatch(cmd)
        print(f"Created resource '{cmd.resource_id}' ({cmd.id})")

    elif config.is_dir():
        typer.Abort("not supported yetls")
        # new_resources = resources.create_new_resource_from_dir(config)

        # for resource_id in new_resources:
        #     typer.echo(f"Created resource {resource_id}")


@subapp.command()
@cli_error_handler
@cli_timer
def set_entry_repo(  # noqa: ANN201, D103
    ctx: typer.Context,
    resource_id: str,
    entry_repo_id: str = typer.Argument(..., help="id for entry-repo"),
    user: Optional[str] = typer.Option(None),
):
    bus = inject_from_ctx(CommandBus, ctx)  # type: ignore [misc]
    entry_repo_uuid = unique_id.parse(entry_repo_id)
    cmd = lex_commands.SetEntryRepoId(
        resourceId=resource_id,
        entryRepoId=entry_repo_uuid,
        user=user or "local admin",
    )
    bus.dispatch(cmd)


@subapp.command()
@cli_error_handler
@cli_timer
def update(  # noqa: ANN201
    ctx: typer.Context,
    config: Path,
    version: int = typer.Option(..., "-v", "--version"),
    message: Optional[str] = typer.Option(None, "-m", "--message"),
    user: Optional[str] = typer.Option(None, "-u", "--user"),
):
    """Update resource config."""  # noqa: D202

    config_dict = jsonlib.load_from_file(config)
    resource_id = config_dict.pop("resource_id")
    if resource_id is None:
        raise ValueError("resource_id must be present")
    resource_name = config_dict.pop("resource_name") or resource_id
    cmd = lex_commands.UpdateResource(
        version=version,
        name=resource_name,
        resourceId=resource_id,
        config=config_dict,
        message=message or "config updated",
        user=user or "local admin",
    )
    print(f"cmd={cmd}")
    bus = inject_from_ctx(CommandBus, ctx)  # type: ignore [misc]
    try:
        bus.dispatch(cmd)
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
def publish(ctx: typer.Context, resource_id: str, version: int):  # noqa: ANN201, D103
    bus = inject_from_ctx(CommandBus, ctx)  # type: ignore [misc]
    try:
        cmd = lex_commands.PublishResource(
            resourceId=resource_id,
            message=f"Publish '{resource_id}",
            user="local admin",
            version=version,
        )
        bus.dispatch(cmd)
    except ResourceAlreadyPublished:
        typer.echo("Resource already published.")
    else:
        typer.echo(f"Resource '{resource_id}' is published ")


@subapp.command()
@cli_error_handler
@cli_timer
def reindex(ctx: typer.Context, resource_id: str):  # noqa: ANN201, D103
    bus = inject_from_ctx(CommandBus, ctx)  # type: ignore [misc]
    cmd = search_commands.ReindexResource(resourceId=resource_id)
    bus.dispatch(cmd)

    typer.echo(f"Successfully reindexed all data in {resource_id}")


# @cli.command("pre_process")
# @click.option("--resource_id", required=True)
# @click.option("--version", required=True)
# @click.option("--filename", required=True)
# @cli_error_handler
# @cli_timer
# def pre_process_resource(resource_id, version, filename):
#     resource = resourcemgr.get_resource(resource_id, version=version)
#     with open(filename, "wb") as fp:
#         processed = indexmgr.pre_process_resource(resource)
#         pickle.dump(processed, fp)


# @cli.command("publish_preprocessed")
# @click.option("--resource_id", required=True)
# @click.option("--version", required=True)
# @click.option("--data", required=True)
# @cli_error_handler
# @cli_timer
# def index_processed(resource_id, version, data):
#     with open(data, "rb") as fp:
#         try:
#             loaded_data = pickle.load(fp)
#             resourcemgr.publish_resource(resource_id, version)
#             indexmgr.reindex(resource_id, version=version, search_entries=loaded_data)
#         except EOFError:
#             click.echo("Something wrong with file")


# @cli.command("reindex_preprocessed")
# @click.option("--resource_id", required=True)
# @click.option("--data", required=True)
# @cli_error_handler
# @cli_timer
# def reindex_preprocessed(resource_id, data):
#     with open(data, "rb") as fp:
#         try:
#             loaded_data = pickle.load(fp)
#             indexmgr.reindex(resource_id, search_entries=loaded_data)
#         except EOFError:
#             click.echo("Something wrong with file")


@subapp.command("list")
@cli_error_handler
@cli_timer
def list_resources(  # noqa: ANN201, D103
    ctx: typer.Context,
    show_published: Optional[bool] = typer.Option(True, "--show-published/--show-all"),
):
    if show_published:
        query = inject_from_ctx(GetPublishedResources, ctx)  # type: ignore [misc]
    else:
        query = inject_from_ctx(GetResources, ctx)  # type: ignore [misc,assignment]
    typer.echo(
        tabulate(
            [
                [resource.resource_id, resource.version, resource.is_published]
                for resource in query.query()
            ],
            headers=["resource_id", "version", "published"],
        )
    )


@subapp.command()
@cli_error_handler
@cli_timer
def show(  # noqa: ANN201, D103
    ctx: typer.Context, resource_id: str, version: Optional[int] = None
):
    repo = inject_from_ctx(lex.ReadOnlyResourceRepository, ctx)  # type: ignore [misc]
    resource = repo.get_by_resource_id(resource_id, version=version)
    #     if version:
    #         resource = database.get_resource_definition(resource_id, version)
    #     else:
    #         resource = database.get_active_or_latest_resource_definition(resource_id)
    if not resource:
        version_str = version or "latest"
        typer.echo(
            f"Can't find resource '{resource_id}', version '{version_str}'", err=True
        )
        raise typer.Exit(3)

    typer.echo(tabulate(((key, value) for key, value in resource.dict().items())))


@subapp.command()
@cli_error_handler
@cli_timer
def set_permissions(  # noqa: ANN201, D103
    ctx: typer.Context,
    resource_id: str,
    version: int,
    level: str,
):
    _bus = inject_from_ctx(CommandBus, ctx)  # type: ignore [misc]


#     # TODO use level
#     permissions = {"write": True, "read": True}
#     resourcemgr.set_permissions(resource_id, version, permissions)
#     click.echo("updated permissions")


@subapp.command()
@cli_error_handler
@cli_timer
def export():  # noqa: ANN201, D103
    raise NotImplementedError()


@subapp.command()
@cli_error_handler
@cli_timer
def delete(  # noqa: ANN201, D103
    ctx: typer.Context,
    resource_id: str,
    user: Optional[str] = typer.Option(None),
    message: Optional[str] = typer.Option(None),
):
    bus = inject_from_ctx(CommandBus, ctx)  # type: ignore [misc]
    cmd = lex_commands.DeleteResource(
        resource_id=resource_id,
        user=user or "local admin",
        message=message or "resource deleted",
    )
    resource = bus.dispatch(cmd)
    typer.echo(f"Deleted resource '{resource_id}' ({resource})")


def init_app(app):  # noqa: ANN201, D103
    app.add_typer(subapp, name="resource")
