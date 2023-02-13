import logging
from typing import Callable
from fastapi import FastAPI

from karp.db_infrastructure import tasks as db_tasks
from karp.main import config


logger = logging.getLogger(__name__)


def create_start_app_handler(app: FastAPI) -> Callable:
    async def start_app() -> None:
        logger.debug("start_app")
        app.state.db = db_tasks.connect_to_db(config.DATABASE_URL)

    return start_app


def create_stop_app_handler(app: FastAPI) -> Callable:
    async def stop_app() -> None:
        logger.debug("stop_app")
        db_tasks.close_db_connection(app.state.db)
        app.state.app_context = None

    return stop_app
