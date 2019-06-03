import logging
import time
import click
import pickle
from flask.cli import FlaskGroup  # pyre-ignore

from .config import MariaDBConfig
from karp import database
from karp.errors import KarpError, ResourceNotFoundError


_logger = logging.getLogger('karp')


def create_app():
    from karp import create_app
    return create_app(MariaDBConfig())


@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    pass


def cli_error_handler(func):
    def func_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KarpError as e:
            _logger.error(e.message)
    return func_wrapper


def cli_timer(func):
    def func_wrapper(*args, **kwargs):
        before_t = time.time()
        result = func(*args, **kwargs)
        click.echo("Command took: %0.1fs" % (time.time() - before_t))
        return result
    return func_wrapper


@cli.command('create')
@click.option('--config', default=None, help='A JSON file containing settings for one resource', required=False)
@click.option('--config_dir', default=None,
              help='A directory containing config files for resource and optionally plugin settings', required=False)
@cli_error_handler
@cli_timer
def create_resource(config, config_dir):
    if config:
        with open(config) as fp:
            new_resource = resourcemgr.create_new_resource_from_file(fp)
        new_resources = [new_resource]
    elif config_dir:
        new_resources = resourcemgr.create_new_resource_from_dir(config_dir)
    else:
        click.echo('Must give either --config or --config_dir')
        click.exceptions.Exit(64)  # Usage error
    for (resource_id, version) in new_resources:
        click.echo('Created version {version} of resource {resource_id}'.format(
            version=version,
            resource_id=resource_id
        ))


@cli.command('import')
@click.option('--resource_id', default=None, help='', required=True)
@click.option('--version', default=None, help='', required=True)
@click.option('--data', default=None, help='', required=True)
@cli_error_handler
@cli_timer
def import_resource(resource_id, version, data):
    count = entrywrite.add_entries_from_file(resource_id, version, data)
    click.echo("Added {count} entries to {resource_id}, version {version}".format(
        count=count,
        version=version,
        resource_id=resource_id
    ))


@cli.command('publish')
@click.option('--resource_id', default=None, help='', required=True)
@click.option('--version', default=None, help='', required=True)
@cli_error_handler
@cli_timer
def publish_resource(resource_id, version):
    resource = resourcemgr.get_resource(resource_id, version=version)
    if resource.active:
        click.echo("Resource already published")
    else:
        indexmgr.publish_index(resource_id, version=version)
        click.echo("Successfully indexed and published all data in {resource_id}, version {version}".format(
            resource_id=resource_id,
            version=version
        ))


@cli.command('reindex')
@click.option('--resource_id', default=None, help='', required=True)
@cli_error_handler
@cli_timer
def reindex_resource(resource_id):
    try:
        resource = resourcemgr.get_resource(resource_id)
        indexmgr.publish_index(resource_id)
        click.echo("Successfully reindexed all data in {resource_id}, version {version}".format(
            resource_id=resource_id,
            version=resource.version)
        )
    except ResourceNotFoundError:
        click.echo("No active version of {resource_id}".format(resource_id=resource_id))


@cli.command('pre_process')
@click.option('--resource_id', required=True)
@click.option('--version', required=True)
@click.option('--filename', required=True)
@cli_error_handler
@cli_timer
def pre_process_resource(resource_id, version, filename):
    resource = resourcemgr.get_resource(resource_id, version=version)
    with open(filename, 'wb') as fp:
        processed = indexmgr.pre_process_resource(resource)
        pickle.dump(processed, fp)


@cli.command('publish_preprocessed')
@click.option('--resource_id', required=True)
@click.option('--version', required=True)
@click.option('--data', required=True)
@cli_error_handler
@cli_timer
def index_processed(resource_id, version, data):
    with open(data, 'rb') as fp:
        try:
            loaded_data = pickle.load(fp)
            resourcemgr.publish_resource(resource_id, version)
            indexmgr.reindex(resource_id, version=version, search_entries=loaded_data)
        except EOFError:
            click.echo('Something wrong with file')


@cli.command('reindex_preprocessed')
@click.option('--resource_id', required=True)
@click.option('--data', required=True)
@cli_error_handler
@cli_timer
def reindex_preprocessed(resource_id, data):
    with open(data, 'rb') as fp:
        try:
            loaded_data = pickle.load(fp)
            indexmgr.reindex(resource_id, search_entries=loaded_data)
        except EOFError:
            click.echo('Something wrong with file')


@cli.command('list')
@click.option('--show-active/--show-all', default=False)
@cli_error_handler
@cli_timer
def list_resources(show_active):
    if show_active:
        resources = resourcemgr.get_available_resources()
    else:
        resources = resourcemgr.get_all_resources()

    click.echo('resource_id version active')
    for resource in resources:
        click.echo('{resource_id} {version} {active}'.format(
            resource_id=resource.resource_id,
            version=resource.version,
            active='y' if resource.active else 'n'
        ))


@cli.command('show')
@click.option('--version', default=None, type=int)
@click.argument('resource_id')
@cli_error_handler
@cli_timer
def show_resource(resource_id, version):
    if version:
        resource = database.get_resource_definition(resource_id, version)
    else:
        resource = database.get_active_or_latest_resource_definition(resource_id)
    if not resource:
        click.echo(
            "Can't find resource '{resource_id}', version '{version}'".format(
                resource_id=resource_id,
                version=version if version else 'active or latest'
            )
        )
        raise click.exceptions.Exit(3)

    click.echo("""
    Resource: {resource.resource_id}
    Version: {resource.version}
    Active: {resource.active}
    Config: {resource.config_file}
    """.format(resource=resource))


@cli.command('set_permissions')
@click.option('--resource_id', required=True)
@click.option('--version', required=True)
@click.option('--level', required=True)
@cli_error_handler
@cli_timer
def set_permissions(resource_id, version, level):
    # TODO use level
    permissions = {
        'write': True,
        'read': True
    }
    resourcemgr.set_permissions(resource_id, version, permissions)
    click.echo('updated permissions')


def export_resource():
    pass


def delete_resource():
    pass
