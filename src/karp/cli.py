import json
import click
from flask.cli import with_appcontext  # pyre-ignore
from distutils.util import strtobool
import logging

from karp import create_app
from .config import MariaDBConfig
import karp.resourcemgr as resourcemgr
import karp.resourcemgr.entrymgr as entrymgr
from karp.errors import KarpError

_logger = logging.getLogger(__name__)
app = create_app(MariaDBConfig)


def cli_error_handler(func):
    def func_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KarpError as e:
            _logger.error(e.message)
    return func_wrapper


@app.cli.command('create')
@click.option('--config', default=None, help='')
@cli_error_handler
def create_resource(config):
    with open(config) as fp:
        resource_id, version = resourcemgr.create_new_resource(fp)
    click.echo("Created version {version} of resource {resource_id}".format(
        version=version,
        resource_id=resource_id
    ))


@app.cli.command('import')
@click.option('--resource_id', default=None, help='')
@click.option('--version', default=None, help='')
@click.option('--data', default=None, help='')
@cli_error_handler
def import_resource(resource_id, version, data):
    resourcemgr.setup_resource_class(resource_id, version)
    with open(data) as fp:
        objs = []
        for line in fp:
            objs.append(json.loads(line))
        entrymgr.add_entries(resource_id, objs, resource_version=version)


@app.cli.command('publish')
@with_appcontext
@click.option('--resource_id', default=None, help='')
@click.option('--version', default=None, help='')
@cli_error_handler
def publish_resource(resource_id, version):
    index_name = resourcemgr.create_index(resource_id, version)
    resourcemgr.reindex(resource_id, index_name, version=version)
    resourcemgr.publish_index(resource_id, index_name)
    resourcemgr.publish_resource(resource_id, version)


@app.cli.command('create_index')
@click.option('--resource_id', default=None, help='')
@cli_error_handler
def create_index(resource_id):
    index_name = resourcemgr.create_index(resource_id)
    click.echo("Created index for resource {resource_id}".format(
        resource_id=resource_id
    ))
    click.echo("New index name: {index_name}".format(
        resource_id=resource_id,
        index_name=index_name
    ))


@app.cli.command('publish_index')
@with_appcontext
@click.option('--resource_id', default=None, help='')
@click.option('--index_name', default=None, help='Name of the index to ')
@cli_error_handler
def publish_index(resource_id, index_name):
    resourcemgr.publish_index(resource_id, index_name)


@app.cli.command('reindex')
@click.option('--resource_id', default=None, help='')
@click.option('--publish_index', 'publish_index_arg', default='', help='')
@cli_error_handler
def reindex(resource_id, publish_index_arg):
    index_name = resourcemgr.create_index(resource_id)
    resourcemgr.reindex(resource_id, index_name)
    click.echo("Successfully reindexed all data to index {index_name}".format(
        index_name=index_name
    ))
    if not publish_index_arg:
        publish_index_arg = click.prompt('Publish new index?', default='n')
    if strtobool(publish_index_arg):
        resourcemgr.publish_index(resource_id, index_name)
        click.echo('Index for {resource_id} published'.format(
            resource_id=resource_id
        ))


@app.cli.command('list_resources')
@click.option('--show_only_active/--show-all', default=False)
@cli_error_handler
def list_resources(show_only_active):
    if show_only_active:
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
