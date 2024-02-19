import typing
from dataclasses import dataclass
from logging.config import dictConfig

try:
    from importlib.metadata import entry_points
except ImportError:
    from importlib_metadata import entry_points  # type: ignore

import injector  # noqa: I001
from sqlalchemy import pool
from sqlalchemy.engine import Engine, create_engine
import logging
import asgi_correlation_id

from karp.lex_infrastructure import GenericLexInfrastructure, LexInfrastructure
from karp.search_infrastructure import (
    Es6SearchIndexMod,
)
from karp.main import config, modules
from karp.main.modules import (
    CommandsMod,
    Db,
    ElasticSearchMod,
    install_auth_service,
)


@dataclass
class AppContext:
    container: injector.Injector
    settings: typing.Dict


def bootstrap_app() -> AppContext:
    env = config.load_env()
    db_url = config.parse_database_url(env)
    es_enabled = env.bool("ELASTICSEARCH_ENABLED", False)
    if es_enabled:
        es_url = env("ELASTICSEARCH_HOST")
    else:
        es_url = env("ELASTICSEARCH_HOST", "")
    settings = {
        "auth.jwt.pubkey.path": env("AUTH_JWT_PUBKEY_PATH", None),
        "auth.name": env("AUTH_NAME", ""),
        "tracking.matomo.idsite": env("TRACKING_MATOMO_IDSITE", None),
        "tracking.matomo.url": env("TRACKING_MATOMO_URL", None),
        "tracking.matomo.token": env("TRACKING_MATOMO_TOKEN", None),
        "es.index_prefix": env("ES_INDEX_PREFIX", None),
    }

    configure_logging(settings=settings)
    engine = _create_db_engine(db_url)
    dependency_injector = _setup_dependency_injection(engine, es_url=es_url)
    _setup_search_context(dependency_injector, settings=settings)
    return AppContext(dependency_injector, settings)


def _create_db_engine(db_url: config.DatabaseUrl) -> Engine:
    kwargs = {}
    if str(db_url).startswith("sqlite"):
        kwargs["poolclass"] = pool.SingletonThreadPool
        kwargs["connect_args"] = {"check_same_thread": False}
    engine_echo = False
    return create_engine(db_url, echo=engine_echo, future=True, **kwargs)


def _setup_dependency_injection(
    engine: Engine,
    es_url: str,
) -> injector.Injector:
    return injector.Injector(
        [
            Db(engine),
            CommandsMod(),
            ElasticSearchMod(es_url),
            LexInfrastructure(),
            GenericLexInfrastructure(),
        ],
        auto_bind=False,
    )


def _setup_search_context(container: injector.Injector, settings: dict) -> None:
    container.binder.install(Es6SearchIndexMod(index_prefix=settings.get("es.index_prefix")))


def configure_logging(settings: dict[str, str]) -> None:
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
                    "handlers": ["json"],
                    "level": "INFO",
                    "propagate": True,
                },
                # third-party package loggers
                "sqlalchemy": {"handlers": ["json"], "level": "WARNING"},
                "uvicorn": {"handlers": ["json"], "level": "INFO"},
            },
        }
    )
