import typing
from dataclasses import dataclass
from logging.config import dictConfig

try:
    from importlib.metadata import entry_points
except ImportError:
    from importlib_metadata import entry_points  # type: ignore

import logging
import sys
from contextlib import contextmanager
from pathlib import Path

import asgi_correlation_id
from elasticsearch import Elasticsearch
from injector import Injector, Module, provider, singleton
from sqlalchemy import pool
from sqlalchemy.engine import URL, Engine, create_engine
from sqlalchemy.orm import Session

from karp.auth.infrastructure import JWTAuthService
from karp.search.infrastructure.es import EsMappingRepository

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
    es_index_prefix = env("ES_INDEX_PREFIX", "")

    settings = {
        "auth.jwt.pubkey.path": jwt_pubkey_path,
        "tracking.matomo.idsite": env("TRACKING_MATOMO_IDSITE", None),
        "tracking.matomo.url": env("TRACKING_MATOMO_URL", None),
        "tracking.matomo.token": env("TRACKING_MATOMO_TOKEN", None),
        "es.url": es_url,
        "es.index_prefix": es_url,
    }

    # Load builtin plugins
    import karp.plugins.link_plugin

    engine = _create_db_engine(DATABASE_URL)

    def configure_dependency_injection(binder):
        es = Elasticsearch(es_url)
        binder.bind(Engine, engine)
        binder.install(ElasticSearchMod(es_url, es_index_prefix))
        if jwt_pubkey_path is not None:
            binder.bind(JWTAuthService, JWTAuthService(Path(jwt_pubkey_path)))

    injector = Injector(configure_dependency_injection)
    return AppContext(injector, settings)


class ElasticSearchMod(Module):
    def __init__(self, url, index_prefix):
        self._url = url
        self._index_prefix = index_prefix

    @provider
    @singleton
    def es(self) -> Elasticsearch:
        logger.info("Creating ES client url=%s", self._url)
        return Elasticsearch(self._url)

    @provider
    @singleton
    def es_mapping_repo(self, es: Elasticsearch) -> EsMappingRepository:
        return EsMappingRepository(es=es, prefix=self._index_prefix)


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


def load_modules(group_name: str, app=None):
    logger.debug("Loading %s", group_name)
    if sys.version_info.minor < 10:  # noqa: YTT204
        karp_modules = entry_points().get(group_name)
    else:
        karp_modules = entry_points(group=group_name)  # type: ignore
    if karp_modules:
        for ep in karp_modules:
            logger.info(
                "Loading '%s' from '%s'",
                ep.name,
                group_name,
                extra={"group_name": group_name, "entry_point_name": ep.name},
            )
            mod = ep.load()
            if app:
                init_app = getattr(mod, "init_app", None)
                if init_app:
                    init_app(app)
