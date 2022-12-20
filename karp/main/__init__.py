import json
from logging.config import dictConfig
import logging
import os
import typing
from dataclasses import dataclass


try:
    from importlib.metadata import entry_points
except ImportError:
    from importlib_metadata import entry_points  # type: ignore

import injector
from json_streams import jsonlib
from sqlalchemy import pool
from sqlalchemy.engine import Engine, create_engine, url as sa_url
import logging
import asgi_correlation_id

from karp.foundation.environs_sqlalchemyurl import sqlalchemy_url
from karp.lex import Lex
from karp.lex_infrastructure import GenericLexInfrastructure, LexInfrastructure
from karp.search_infrastructure import (
    GenericSearchInfrastructure,
    Es6SearchIndexMod,
    GenericSearchIndexMod,
    SearchInfrastructure,
)
from karp.main import config, modules
from karp.main.modules import (
    CommandBusMod,
    Db,
    EventBusMod,
    ElasticSearchMod,
    install_auth_service,
)
from karp.search import Search


@dataclass
class AppContext:
    container: injector.Injector
    settings: typing.Dict


def bootstrap_app(container=None) -> AppContext:
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
    # if n ot container:
    # container = AppContainer()
    # container.config.core.logging.from_value(_logging_config())
    # container.config.db.url.from_value(config.DB_URL)
    # container.config.search_service.type.from_env(
    # "SEARCH_CONTEXT", "sql_search_service"
    # )
    # bus = container.bus()
    # bus.handle(events.AppStarted())  # needed? ?
    configure_logging(settings=settings)
    # logging.config.dictConfig(_logging_config())  # type: ignore
    search_service = env("SEARCH_CONTEXT", "sql_search_service")
    engine = _create_db_engine(db_url)
    dependency_injector = _setup_dependency_injection(engine, es_url=es_url)
    _setup_search_context(dependency_injector, search_service, settings=settings)
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
            CommandBusMod(),
            EventBusMod(),
            ElasticSearchMod(es_url),
            Lex(),
            LexInfrastructure(),
            GenericLexInfrastructure(),
            Search(),
            GenericSearchInfrastructure(),
            SearchInfrastructure(),
            # SearchServiceMod(search_service),
        ],
        auto_bind=False,
    )


def _setup_search_context(
    container: injector.Injector, search_service: str, settings: dict
) -> None:
    if search_service.lower() == "es6_search_service":
        container.binder.install(
            Es6SearchIndexMod(index_prefix=settings.get("es.index_prefix"))
        )
    else:
        container.binder.install(GenericSearchIndexMod())


def configure_logging(settings: dict[str, str]) -> None:
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
                    # 'datefmt':  '%H:%M:%S',
                    "format": "%(levelname)s:\t\b%(asctime)s %(name)s:%(lineno)d [%(correlation_id)s] %(message)s",
                },
                "json": {
                    "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    # 'format': '%(message)s',
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
                    # "level": 'DEBUG',
                    "stream": "ext://sys.stderr",
                },
                "json": {
                    "class": "logging.StreamHandler",
                    "filters": ["correlation_id"],
                    "formatter": "json",
                },
                # "email": {
                #     "class": "logging.handlers.SMTPHandler",
                #     "mailhost": "localhost",
                #     "formatter": "standard",
                #     "level": "WARNING",
                #     "fromaddr": config.LOG_MAIL_FROM,
                #     "toaddrs": config.LOG_MAIL_TOS,
                #     "subject": "Error in Karp backend!",
                # },
            },
            "loggers": {
                "karp": {
                    "handlers": ["json"],  # ["console", "email"],
                    "level": "DEBUG",  # config.CONSOLE_LOG_LEVEL,
                    "propagate": True,
                },
                # third-party package loggers
                "sqlalchemy": {"handlers": ["json"], "level": "WARNING"},
                "uvicorn.access": {"handlers": ["json"], "level": "INFO"},
            },
        }
    )


# def bootstrap(
#    resource_uow: unit_of_work.ResourceUnitOfWork = None,
#    entry_uows: unit_of_work.EntriesUnitOfWork = None,
#    authservice: auth_service.AuthService = None,
#    index_uow: unit_of_work.IndexUnitOfWork = None,
#    entry_uow_factory: unit_of_work.EntryUowFactory = None,
#    raise_on_all_errors: bool = False,
# ) -> messagebus.MessageBus:
#    setup_logging()
#    load_infrastructure()
#    if authservice is None:
#        authservice = auth_service.AuthService.create(config.AUTH_CONTEXT)
#    if resource_uow is None:
#        resource_uow = sql_unit_of_work.SqlResourceUnitOfWork()
#    if entry_uows is None:
#        entry_uows = unit_of_work.EntriesUnitOfWork()
#    if entry_uow_factory is None:
#        entry_uow_factory = unit_of_work.DefaultEntryUowFactory()
#    if index_uow is None:
#        index_uow = unit_of_work.IndexUnitOfWork.create(config.SEARCH_CONTEXT)
#    bus = messagebus.MessageBus(
#        resource_uow=resource_uow,
#        entry_uows=entry_uows,
#        # auth_service=authservice,
#        search_service_uow=index_uow,
#        entry_uow_factory=entry_uow_factory,
#        raise_on_all_errors=raise_on_all_errors,
#    )
#    bus.handle(events.AppStarted())  # needed? ?
#    return bus


def setup_logging():

    # Clear Gunicorn access log to remove duplicate requests logging
    # logging.getLogger("gunicorn.access").handlers.clear()
    logging.basicConfig(
        format="%(asctime)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        level=logging.INFO,
    )
    logger = logging.getLogger("karp")
    logger.setLevel(logging.INFO)
    # structlog.configure(
    #     processors=[
    #         structlog.stdlib.add_log_level,
    #         structlog.threadlocal.merge_threadlocal,
    #         structlog.processors.TimeStamper(fmt="iso"),
    #         structlog.processors.JSONRenderer(
    #             serializer=json.dumps, sort_keys=True),
    #     ],
    #     wrapper_class=structlog.stdlib.BoundLogger,
    #     context_class=dict,
    #     cache_logger_on_first_use=True,
    #     logger_factory=structlog.stdlib.LoggerFactory(),
    # )
    logger = logging.getLogger(__name__)
    # if app.config.get("LOG_TO_SLACK"):
    #     slack_handler = slack_logging.get_slack_logging_handler(
    #         app.config.get("SLACK_SECRET")
    #     )
    #     logger.addHandler(slack_handler)
    # console_handler = logging.StreamHandler()
    # formatter = logging.Formatter(
    #     "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    # )
    # console_handler.setFormatter(formatter)
    # logger.setLevel(logging.DEBUG)
    # logger.addHandler(console_handler)
    return logger


def load_infrastructure():
    modules.load_modules("karp.infrastructure")
