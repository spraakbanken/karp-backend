import logging
import typing

try:
    from importlib.metadata import entry_points
except ImportError:
    from importlib_metadata import entry_points  # type: ignore

from karp.application import config
from karp.domain import events
from karp.infrastructure.jwt import jwt_auth_service
from karp.infrastructure.sql import sql_unit_of_work
from karp.services import auth_service, messagebus, unit_of_work


def bootstrap(
    resource_uow: unit_of_work.ResourceUnitOfWork = None,
    entry_uows: unit_of_work.EntriesUnitOfWork = None,
    authservice: auth_service.AuthService = None,
    index_uow: unit_of_work.IndexUnitOfWork = None,
    entry_uow_factory: unit_of_work.EntryUowFactory = None,
    raise_on_all_errors: bool = False,
) -> messagebus.MessageBus:
    setup_logging()
    load_infrastructure()
    if authservice is None:
        authservice = auth_service.AuthService.create(config.AUTH_CONTEXT)
    if resource_uow is None:
        resource_uow = sql_unit_of_work.SqlResourceUnitOfWork()
    if entry_uows is None:
        entry_uows = unit_of_work.EntriesUnitOfWork()
    if entry_uow_factory is None:
        entry_uow_factory = unit_of_work.DefaultEntryUowFactory()
    if index_uow is None:
        index_uow = unit_of_work.IndexUnitOfWork.create(config.SEARCH_CONTEXT)
    bus = messagebus.MessageBus(
        resource_uow=resource_uow,
        entry_uows=entry_uows,
        auth_service=authservice,
        index_uow=index_uow,
        entry_uow_factory=entry_uow_factory,
        raise_on_all_errors=raise_on_all_errors,
    )
    bus.handle(events.AppStarted())  # needed? ?
    return bus


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
