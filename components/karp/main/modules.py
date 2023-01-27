import logging
from pathlib import Path
import threading
from typing import Dict, Type
import sys

try:
    from importlib.metadata import entry_points
except ImportError:
    # used if python == 3.9
    from importlib_metadata import entry_points  # type: ignore

import elasticsearch
import injector
from injector import Provider, T
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import Session, sessionmaker

from karp.foundation.commands import CommandBus, InjectorCommandBus
from karp.foundation.events import EventBus, InjectorEventBus
from karp.auth_infrastructure import (
    AuthInfrastructure,
    TestAuthInfrastructure,
    JwtAuthInfrastructure,
)


# from foundation.events import EventBus, InjectorEventBus, RunAsyncHandler
# from foundation.locks import Lock, LockFactory
#
# from customer_relationship import CustomerRelationshipConfig
# from main.async_handler_task import async_handler_generic_task
# from main.redis import RedisLock
# from payments import PaymentsConfig


logger = logging.getLogger(__name__)


class RequestScope(injector.Scope):
    REGISTRY_KEY = "RequestScopeRegistry"

    def configure(self) -> None:
        self._locals = threading.local()

    def enter(self) -> None:
        logger.warning("entering request scope")
        assert not hasattr(self._locals, self.REGISTRY_KEY)
        setattr(self._locals, self.REGISTRY_KEY, {})

    def exit(self) -> None:
        logger.warning("exiting request scope")
        for key, provider in getattr(self._locals, self.REGISTRY_KEY).items():
            provider.get(self.injector).close()
            delattr(self._locals, repr(key))

        delattr(self._locals, self.REGISTRY_KEY)

    def __enter__(self) -> None:
        self.enter()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        self.exit()

    def get(self, key: Type[T], provider: Provider[T]) -> Provider[T]:
        try:
            return getattr(self._locals, repr(key))  # type: ignore
        except AttributeError:
            provider = injector.InstanceProvider(provider.get(self.injector))
            setattr(self._locals, repr(key), provider)
            try:
                registry = getattr(self._locals, self.REGISTRY_KEY)
            except AttributeError:
                raise Exception(
                    f"{key} is request scoped, but no RequestScope entered!"
                )
            registry[key] = provider
            return provider


request = injector.ScopeDecorator(RequestScope)


class CommandBusMod(injector.Module):
    @injector.provider
    def command_bus(self, inj: injector.Injector) -> CommandBus:
        return InjectorCommandBus(inj)


class EventBusMod(injector.Module):
    @injector.provider
    def event_bus(self, inj: injector.Injector) -> EventBus:
        return InjectorEventBus(inj)


class Db(injector.Module):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    # @request
    @injector.provider
    def connection(self) -> Connection:
        return self._engine.connect()

    # @request
    @injector.provider
    def session(self, connection: Connection) -> Session:
        return Session(bind=connection)

    # @request
    @injector.provider
    def session_factory(self) -> sessionmaker:
        return sessionmaker(bind=self._engine)


class ElasticSearchMod(injector.Module):
    def __init__(self, es_url: str) -> None:
        self._url = es_url

    @injector.provider
    @injector.singleton
    def es(self) -> elasticsearch.Elasticsearch:
        logger.info("Creating ES client url=%s", self._url)
        return elasticsearch.Elasticsearch(self._url)


TEST_AUTH_SERVICE = "DUMMY_AUTH"


def install_auth_service(container: injector.Injector, settings: Dict[str, str]):
    auth_service_name = settings.get("auth.name", "")
    container.binder.install(AuthInfrastructure())

    if auth_service_name.upper() == TEST_AUTH_SERVICE:
        container.binder.install(TestAuthInfrastructure())
    else:
        container.binder.install(
            JwtAuthInfrastructure(Path(settings["auth.jwt.pubkey.path"]))
        )


def request_configuration(conn: Connection, session: Session):
    def configure_request_container(binder):
        binder.bind(Connection, to=injector.InstanceProvider(conn))
        binder.bind(Session, to=injector.InstanceProvider(session))

    return configure_request_container


def load_modules(group_name: str, app=None):
    logger.debug("Loading %s", group_name)
    if sys.version_info.minor < 10:
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
