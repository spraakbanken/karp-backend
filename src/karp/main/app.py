import logging
import typing
from dataclasses import dataclass
from logging.config import dictConfig

import asgi_correlation_id

from karp.globals import create_db_engine, create_es

from .config import env

logger = logging.getLogger(__name__)


@dataclass
class AppContext:
    settings: typing.Dict


def bootstrap_app() -> AppContext:
    configure_logging()
    create_db_engine()
    create_es()

    settings = {
        "tracking.matomo.idsite": env("TRACKING_MATOMO_IDSITE", None),
        "tracking.matomo.url": env("TRACKING_MATOMO_URL", None),
        "tracking.matomo.token": env("TRACKING_MATOMO_TOKEN", None),
    }

    return AppContext(settings)


class NoStackTraceHandler(logging.StreamHandler):
    """
    Use this if a library does logger.exception and we don't want to see the stack trace
    """

    def emit(self, record):
        if record.exc_info:
            record.msg = record.getMessage() + f" ({record.exc_info[0]!s})"
            record.exc_info = None
        super().emit(record)


def configure_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "correlation_id": {
                    "()": asgi_correlation_id.CorrelationIdFilter,
                    "uuid_length": 32,
                }
            },
            "formatters": {
                "console": {
                    "class": "logging.Formatter",
                    "format": "%(levelname)s:\t\b%(asctime)s %(name)s:%(lineno)d [%(correlation_id)s] %(message)s",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "filters": ["correlation_id"],
                    "formatter": "console",
                    "stream": "ext://sys.stdout",
                },
                # This handler does not print stacktraces
                "nostack": {
                    "class": "karp.main.app.NoStackTraceHandler",
                    "filters": ["correlation_id"],
                    "formatter": "console",
                },
            },
            "loggers": {
                "karp": {
                    "level": "INFO",
                    "propagate": True,
                    "handlers": ["console"],
                },
                # third-party package loggers
                "sqlalchemy": {"level": "WARNING", "handlers": ["console"]},
                "uvicorn": {"level": "INFO", "handlers": ["console"]},
                "asgi_matomo": {"level": "WARNING", "handlers": ["nostack"]},
            },
        }
    )
