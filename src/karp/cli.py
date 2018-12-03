import json
import click
from flask.cli import with_appcontext  # pyre-ignore

from karp import create_app
from .config import MariaDBConfig
import karp.resourcemgr as resourcemgr

app = create_app(MariaDBConfig)


@app.cli.command('create')
@click.option('--config', default=None, help='')
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
def import_resource(resource_id, version, data):
    resourcemgr.setup_resource_class(resource_id, version)
    with open(data) as fp:
        objs = []
        for line in fp:
            objs.append(json.loads(line))
        resourcemgr.add_entries(resource_id, version, objs)


@app.cli.command('publish')
@with_appcontext
@click.option('--resource_id', default=None, help='')
@click.option('--version', default=None, help='')
def publish_resource(resource_id, version):
    resourcemgr.publish_resource(resource_id, version)


@app.cli.command('create_index')
@click.option('--resource_id', default=None, help='')
@click.option('--version', default=None, help='')
def create_index(resource_id, version):
    index_name = resourcemgr.create_index(resource_id, version=version)
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
def publish_index(resource_id, index_name):
    resourcemgr.publish_index(resource_id, index_name)


@app.cli.command('reindex')
@click.option('--resource_id', default=None, help='')
@click.option('--version', default=None, help='')
def reindex(resource_id, version):
    index_name = resourcemgr.create_index(resource_id, version=version)
    resourcemgr.reindex(resource_id, index_name, version=version)
    click.echo("Successfully reindexed all data to index {index_name}".format(
        index_name=index_name
    ))

# Future stuff
# export resource
# list resources (with filters)
# delete resource
# unpublish resource
