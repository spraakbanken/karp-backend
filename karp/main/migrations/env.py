import logging
import os

import alembic
from sqlalchemy import engine_from_config, pool, create_engine
from logging.config import fileConfig

from karp.main import config as karp_config
from karp.db_infrastructure import db

# from karp.migration_helper import entry_tables, history_tables, database_uri


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = alembic.context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)  # type: ignore
logger = logging.getLogger('alembic.env')

karp_env = karp_config.load_env()
DATABASE_URL = str(karp_config.parse_sqlalchemy_url(karp_env))
DATABASE_NAME = karp_config.parse_sqlalchemy_database_name(karp_env)


# def include_object(object, name, type_, reflected, compare_to):
#     return not (type_ == "table" and (name in entry_tables or name in history_tables))


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # handle testing config for migrations
    if os.environ.get("TESTING"):
        # connect to primary db
        default_engine = create_engine(
            str(karp_config.parse_sqlalchemy_url_wo_db(karp_env)),
            isolation_level="AUTOCOMMIT"
        )
        # drop testing db if it exists and create a fresh one
        with default_engine.connect() as default_conn:
            default_conn.execute(f"DROP DATABASE IF EXISTS {DATABASE_NAME}")
            default_conn.execute(f"CREATE DATABASE {DATABASE_NAME}")

    connectable = config.attributes.get('connection', None)
    config.set_main_option("sqlalchemy.url", DATABASE_URL)

    if connectable is None:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section),  # type: ignore
            prefix="sqlalchemy.",
            poolclass=pool.NullPool
        )

    with connectable.connect() as connection:
        alembic.context.configure(
            connection=connection,
            target_metadata=db.metadata,
            # include_object=include_object,
            compare_type=True,
        )

        with alembic.context.begin_transaction():
            alembic.context.run_migrations()


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    """

    if os.environ.get("TESTING"):
        raise RuntimeError(
            "Running testing migrations offline currently not permitted.")

    alembic.context.configure(url=DATABASE_URL)
    with alembic.context.begin_transaction():
        alembic.context.run_migrations()


if alembic.context.is_offline_mode():
    logger.info("Running migrations offline")
    run_migrations_offline()
else:
    logger.info("Running migrations online")
    run_migrations_online()
