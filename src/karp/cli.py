import json
import click
import os
from .app import create_app
import karp.database as database
from .models import setup_resource_class, create_new_resource, publish_resource

user = os.environ["MARIADB_USER"]
passwd = os.environ["MARIADB_PASSWORD"]
dbhost = os.environ["MARIADB_HOST"]
dbname = os.environ["MARIADB_DATABASE"]

app = create_app({
    'SQLALCHEMY_DATABASE_URI': 'mysql://%s:%s@%s/%s' % (user, passwd, dbhost, dbname),
    'setup_database': False
})


@app.cli.command('create')
@click.option('--config', default=None, help='')
def create_resource(config):
    resource_id, version = create_new_resource(config)
    click.echo('Created version %s of resource %s' % (version, resource_id))


@app.cli.command('import')
@click.option('--resource_id', default=None, help='')
@click.option('--version', default=None, help='')
@click.option('--data', default=None, help='')
def import_resource(resource_id, version, data):
    setup_resource_class(resource_id, version)
    with open(data) as fp:
        for line in fp:
            obj = json.loads(line)
            database.add_entry(resource_id, obj)


@app.cli.command('publish')
@click.option('--resource_id', default=None, help='')
@click.option('--version', default=None, help='')
def publish_resource_tmp(resource_id, version):
    publish_resource(resource_id, version)


# Future stuff
# export resource
# list resources (with filters)
# delete resource
# unpublish resource
