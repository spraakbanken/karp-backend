import json
import click
from karp.web import app
from karp.web import Entry
from karp.web import db


@app.cli.command('entries')
@click.option('--size', default=None, help='Number of entries to return')
def get_entries(size):
    entries = Entry.query.all()
    click.echo("Found: %s entries" % len(entries))
    click.echo(json.dumps([entry.serialize for entry in entries], indent=4))


@app.cli.command('add')
@click.option('--value', default="hm", help='Value of entry to add')
def add_entry(value):
    entry = Entry(value=value)
    db.session.add(entry)
    db.session.commit()
    click.echo("Added %s" % value)
