import json
import click
from karp.web import app
import karp.database as database


@app.cli.command('entries')
@click.option('--size', default=None, help='Number of entries to return')
def get_entries(size):
    entries = database.get_entries()
    click.echo("Found: %s entries" % len(entries))
    click.echo(json.dumps([entry.serialize for entry in entries], indent=4))


@app.cli.command('add')
@click.option('--value', default="hm", help='Value of entry to add')
def add_entry(value):
    database.add_entry(value)
    click.echo("Added %s" % value)
