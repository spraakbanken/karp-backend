import logging
import os
from typing import Union

from karp.db_infrastructure import Database

from karp.main.config import DATABASE_URL, DatabaseUrl


logger = logging.getLogger(__name__)


def connect_to_db(db_url: Union[str, DatabaseUrl]) -> Database:
    try:
        return Database(db_url)
    except Exception as e:
        logger.warn("--- DB CONNECTION ERROR ---")
        logger.warn(e)
        logger.warn("--- DB CONNECTION ERROR ---")


def close_db_connection(database: Database) -> None:
    try:
        database.disconnect()
    except Exception as e:
        logger.warn("--- DB DISCONNECT ERROR ---")
        logger.warn(e)
        logger.warn("--- DB DISCONNECT ERROR ---")
