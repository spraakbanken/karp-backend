import json
import click
import os
from flask.cli import with_appcontext

import karp.database as database
from . import models

user = os.environ["MARIADB_USER"]
passwd = os.environ["MARIADB_PASSWORD"]
dbhost = os.environ["MARIADB_HOST"]
dbname = os.environ["MARIADB_DATABASE"]

app_config = {
    'SQLALCHEMY_DATABASE_URI': 'mysql://%s:%s@%s/%s' % (user, passwd, dbhost, dbname),
    'setup_database': False
}


@click.command('create')
@with_appcontext
@click.option('--config', default=None, help='')
def create_resource(config):
    resource_id, version = models.create_new_resource(config)
    click.echo('Created version %s of resource %s' % (version, resource_id))


@click.command('import')
@with_appcontext
@click.option('--resource_id', default=None, help='')
@click.option('--version', default=None, help='')
@click.option('--data', default=None, help='')
def import_resource(resource_id, version, data):
    models.setup_resource_class(resource_id, version)
    with open(data) as fp:
        objs = []
        for line in fp:
            objs.append(json.loads(line))
        database.add_entries(resource_id, objs)


@click.command('publish')
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
