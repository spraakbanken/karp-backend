import json
import click
from flask.cli import with_appcontext  # pyre-ignore

import karp.database as database
from . import models
from karp import create_app
from .config import MariaDBConfig

app = create_app(MariaDBConfig)


@app.cli.command('create')
@click.option('--config', default=None, help='')
def create_resource(config):
    with open(config) as fp:
        resource_id, version = models.create_new_resource(fp)
    click.echo("Created version {version} of resource {resource_id}".format(
        version=version,
        resource_id=resource_id
    ))


@app.cli.command('import')
@click.option('--resource_id', default=None, help='')
@click.option('--version', default=None, help='')
@click.option('--data', default=None, help='')
def import_resource(resource_id, version, data):
    models.setup_resource_class(resource_id, version)
    with open(data) as fp:
        objs = []
        for line in fp:
            objs.append(json.loads(line))
        database.add_entries(resource_id, version, objs)


@app.cli.command('publish')
@with_appcontext
@click.option('--resource_id', default=None, help='')
@click.option('--version', default=None, help='')
def publish_resource(resource_id, version):
    models.publish_resource(resource_id, version)

# Future stuff
# export resource
# list resources (with filters)
# delete resource
# unpublish resource
