import logging  # noqa: D100, I001
import os  # noqa: F401
from typing import Union

from karp.db_infrastructure import Database

from karp.main.config import DATABASE_URL, DatabaseUrl  # noqa: F401


logger = logging.getLogger(__name__)


def connect_to_db(db_url: Union[str, DatabaseUrl]) -> Database:  # noqa: D103
    try:
        return Database(db_url)
    except Exception as e:  # noqa: BLE001
        logger.warn("--- DB CONNECTION ERROR ---")
        logger.warn(e)
        logger.warn("--- DB CONNECTION ERROR ---")


def close_db_connection(database: Database) -> None:  # noqa: D103
    try:
        database.disconnect()
    except Exception as e:  # noqa: BLE001
        logger.warn("--- DB DISCONNECT ERROR ---")
        logger.warn(e)
        logger.warn("--- DB DISCONNECT ERROR ---")
