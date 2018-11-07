import json
import click
import os
from .app import create_app
import karp.database as database

user = os.environ["MARIADB_USER"]
passwd = os.environ["MARIADB_PASSWORD"]
dbhost = os.environ["MARIADB_HOST"]
dbname = os.environ["MARIADB_DATABASE"]

app = create_app({
    'SQLALCHEMY_DATABASE_URI': 'mysql://%s:%s@%s/%s' % (user, passwd, dbhost, dbname)
})


@app.cli.command('entries')
@click.option('--size', default=None, help='Number of entries to return')
def get_entries(size):
    entries = database.get_entries()
    click.echo("Found: %s entries" % len(entries))
    click.echo(json.dumps([entry.serialize for entry in entries], indent=4))


@app.cli.command('add')
@click.argument('value')
def add_entry(value):
    database.add_entry(value)
    click.echo("Added %s" % value)
