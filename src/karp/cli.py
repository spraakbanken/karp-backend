import logging
import click
from flask.cli import FlaskGroup

from .config import MariaDBConfig
import karp.resourcemgr as resourcemgr
import karp.resourcemgr.entrywrite as entrywrite
import karp.indexmgr as indexmgr
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


@cli.command('create')
@click.option('--config', default=None, help='', required=True)
@cli_error_handler
def create_resource(config):
    with open(config) as fp:
        resource_id, version = resourcemgr.create_new_resource(fp)
    click.echo("Created version {version} of resource {resource_id}".format(
        version=version,
        resource_id=resource_id
    ))


@cli.command('import')
@click.option('--resource_id', default=None, help='', required=True)
@click.option('--version', default=None, help='', required=True)
@click.option('--data', default=None, help='', required=True)
@cli_error_handler
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


@cli.command('list')
@click.option('--show-active/--show-all', default=False)
@cli_error_handler
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


def export_resource():
    pass


def delete_resource():
    pass
