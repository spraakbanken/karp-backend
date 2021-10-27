import logging
import os
import typing
from dataclasses import dataclass

from marshmallow.fields import URL

try:
    from importlib.metadata import entry_points
except ImportError:
    from importlib_metadata import entry_points  # type: ignore

import dotenv
import environs
import injector
from sqlalchemy.engine import Engine, create_engine, url as sa_url

from karp.foundation.environs_sqlalchemyurl import sqlalchemy_url
from karp.lex import Lex
from karp.lex_infrastructure import LexInfrastructure
from karp.main.modules import CommandBusMod, Db, EventBusMod
from karp.search import Search


@dataclass
class AppContext:
    injector: injector.Injector


def bootstrap_app(container=None) -> AppContext:
    config_path = os.environ.get("CONFIG_PATH", ".env")
    print(f"loading config from '{config_path}'")
    # dotenv.load_dotenv(config_path)
    env = environs.Env()
    env.read_env(config_path)
    env.add_parser('sqlalchemy_url', sqlalchemy_url)
    try:
        db_url = env.sqlalchemy_url('DB_URL')
    except environs.EnvError:
        db_url = sa_url.URL.create(
            drivername=env('DB_DRIVER', 'mysql+pymysql'),
            username=env('DB_USER', None),
            password=env('DB_PASSWORD', None),
            host=env('DB_HOST', None),
            port=env.int('DB_PORT', None),
            database=env('DB_DATABASE', None),
            query={'charset': 'utf8mb4'}
        )
    # if n ot container:
    # container = AppContainer()
    # container.config.core.logging.from_value(_logging_config())
    # container.config.db.url.from_value(config.DB_URL)
    # container.config.search_service.type.from_env(
    # "SEARCH_CONTEXT", "sql_search_service"
    # )
    # container.config.search_service.elasticsearch_hosts.from_value(
    # config.ELASTICSEARCH_HOST
    # )
    # container.config.debug.from_value(config.DEBUG)
    # container.core.init_resources()
    # bus = container.bus()
    # bus.handle(events.AppStarted())  # needed? ?

    engine = create_engine(db_url)
    dependency_injector = _setup_dependency_injection(engine)
    return AppContext(dependency_injector)


def _setup_dependency_injection(engine: Engine) -> injector.Injector:
    return injector.Injector(
        [
            Db(engine),
            CommandBusMod(),
            EventBusMod(),
            Lex(),
            LexInfrastructure(),
            Search(),
        ],
        auto_bind=False,
    )


def _logging_config() -> typing.Dict[str, typing.Any]:
    return {
        "version": 1,
        "formatters": {
            "standard": {
                "format": "%(asctime)s-%(levelname)s-%(name)s-%(process)d::%(module)s|%(lineno)s:: %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "stream": "ext://sys.stderr",
            },
            "email": {
                "class": "logging.handlers.SMTPHandler",
                "mailhost": "localhost",
                "formatter": "standard",
                "level": "WARNING",
                "fromaddr": config.LOG_MAIL_FROM,
                "toaddrs": config.LOG_MAIL_TOS,
                "subject": "Error in Karp backend!",
            },
        },
        "loggers": {
            "karp": {
                "handlers": ["console", "email"],
                "level": config.CONSOLE_LOG_LEVEL,
            }
        },
    }


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
    logger = logging.getLogger("karp")
    # if app.config.get("LOG_TO_SLACK"):
    #     slack_handler = slack_logging.get_slack_logging_handler(
    #         app.config.get("SLACK_SECRET")
    #     )
    #     logger.addHandler(slack_handler)
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    logger.setLevel(config.CONSOLE_LOG_LEVEL)
    logger.addHandler(console_handler)
    return logger


def load_infrastructure():
    logger = logging.getLogger("karp")
    print("load_infrastructure")
    for ep in entry_points()["karp.infrastructure"]:
        logger.info("Loading infrastructure module: %s", ep.name)
        print("Loading infrastructure module: %s" % ep.name)
        ep.load()
