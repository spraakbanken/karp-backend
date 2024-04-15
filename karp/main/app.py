import logging
import sys
import typing
from contextlib import contextmanager
from dataclasses import dataclass
from logging.config import dictConfig
from pathlib import Path

import asgi_correlation_id
from elasticsearch import Elasticsearch
from injector import Injector, Module, provider, singleton
from sqlalchemy import pool
from sqlalchemy.engine import URL, Engine, create_engine
from sqlalchemy.orm import Session

from karp.auth.infrastructure import JWTAuthService

from .config import DATABASE_URL, env

logger = logging.getLogger(__name__)


@dataclass
class AppContext:
    injector: Injector
    settings: typing.Dict


def bootstrap_app() -> AppContext:
    configure_logging()

    jwt_pubkey_path = env("AUTH_JWT_PUBKEY_PATH", None)
    es_url = env("ELASTICSEARCH_HOST")

    settings = {
        "tracking.matomo.idsite": env("TRACKING_MATOMO_IDSITE", None),
        "tracking.matomo.url": env("TRACKING_MATOMO_URL", None),
        "tracking.matomo.token": env("TRACKING_MATOMO_TOKEN", None),
    }

    engine = _create_db_engine(DATABASE_URL)

    def configure_dependency_injection(binder):
        binder.bind(Engine, engine)
        binder.install(ElasticSearchMod(es_url))
        if jwt_pubkey_path is not None:
            binder.bind(JWTAuthService, JWTAuthService(Path(jwt_pubkey_path)))

    injector = Injector(configure_dependency_injection)
    return AppContext(injector, settings)


class ElasticSearchMod(Module):
    def __init__(self, url):
        self._url = url

    @provider
    @singleton
    def es(self) -> Elasticsearch:
        logger.info("Creating ES client url=%s", self._url)
        return Elasticsearch(self._url)


def _create_db_engine(db_url: URL) -> Engine:
    kwargs = {}
    if str(db_url).startswith("sqlite"):
        kwargs["poolclass"] = pool.SingletonThreadPool
        kwargs["connect_args"] = {"check_same_thread": False}
    engine_echo = False
    return create_engine(db_url, echo=engine_echo, future=True, **kwargs)


def configure_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": True,
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
                "json": {
                    "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "format": "%(asctime)s %(levelname)s %(name)s %(process)d %(funcName)s %(lineno)d %(message)s",
                },
                "standard": {
                    "format": "%(asctime)s-%(levelname)s-%(name)s-%(process)d::%(module)s|%(lineno)s:: %(message)s",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "filters": ["correlation_id"],
                    "formatter": "console",
                    "stream": "ext://sys.stderr",
                },
                "json": {
                    "class": "logging.StreamHandler",
                    "filters": ["correlation_id"],
                    "formatter": "json",
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
            },
        }
    )


def with_new_session(injector: Injector):
    session = Session(bind=injector.get(Engine), close_resets_only=True)
    # Note on close_resets_only=False: this will detect cases where we call close()
    # while another piece of code is still using the session. If you plan to remove this,
    # be careful about the cache in SqlResourceRepository.

    def configure_child(binder):
        binder.bind(Session, to=session)

    return injector.create_child_injector(configure_child)


@contextmanager
def new_session(injector: Injector):
    injector = with_new_session(injector)
    with injector.get(Session) as session:
        yield injector
