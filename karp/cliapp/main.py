import click

from flask.cli import FlaskGroup  # pyre-ignore
import dotenv

dotenv.load_dotenv(".env", verbose=True)

from .config import MariaDBConfig


def create_app():

    from karp import create_app

    return create_app(MariaDBConfig())


@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    pass
