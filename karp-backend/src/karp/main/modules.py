import logging  # noqa: D100, I001
from pathlib import Path
import threading
from typing import Dict, Type
import sys

try:
    from importlib.metadata import entry_points
except ImportError:
    # used if python == 3.9
    from importlib_metadata import entry_points  # type: ignore

import elasticsearch  # noqa: I001
import injector
from injector import Provider, T
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import Session, sessionmaker

from karp.command_bus import CommandBus, InjectorCommandBus
from karp.foundation.events import EventBus, InjectorEventBus
from karp.auth_infrastructure import (
    AuthInfrastructure,
    JwtAuthInfrastructure,
)

logger = logging.getLogger(__name__)


class RequestScope(injector.Scope):  # noqa: D101
    REGISTRY_KEY = "RequestScopeRegistry"

    def configure(self) -> None:  # noqa: D102
        self._locals = threading.local()

    def enter(self) -> None:  # noqa: D102
        logger.warning("entering request scope")
        assert not hasattr(self._locals, self.REGISTRY_KEY)  # noqa: S101
        setattr(self._locals, self.REGISTRY_KEY, {})

    def exit(self) -> None:  # noqa: A003, D102
        logger.warning("exiting request scope")
        for key, provider in getattr(self._locals, self.REGISTRY_KEY).items():
            provider.get(self.injector).close()
            delattr(self._locals, repr(key))

        delattr(self._locals, self.REGISTRY_KEY)

    def __enter__(self) -> None:  # noqa: D105
        self.enter()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore  # noqa: D105
        self.exit()

    def get(self, key: Type[T], provider: Provider[T]) -> Provider[T]:  # noqa: D102
        try:
            return getattr(self._locals, repr(key))  # type: ignore
        except AttributeError:
            provider = injector.InstanceProvider(provider.get(self.injector))
            setattr(self._locals, repr(key), provider)
            try:
                registry = getattr(self._locals, self.REGISTRY_KEY)
            except AttributeError:
                raise Exception(  # noqa: B904
                    f"{key} is request scoped, but no RequestScope entered!"
                )
            registry[key] = provider
            return provider


request = injector.ScopeDecorator(RequestScope)


class CommandBusMod(injector.Module):  # noqa: D101
    @injector.provider
    def command_bus(self, inj: injector.Injector) -> CommandBus:  # noqa: D102
        return InjectorCommandBus(inj)


class EventBusMod(injector.Module):  # noqa: D101
    @injector.provider
    def event_bus(self, inj: injector.Injector) -> EventBus:  # noqa: D102
        return InjectorEventBus(inj)


class Db(injector.Module):  # noqa: D101
    def __init__(self, engine: Engine) -> None:  # noqa: D107
        self._engine = engine

    @injector.provider
    def connection(self) -> Connection:  # noqa: D102
        return self._engine.connect()

    @injector.provider
    def session(self, connection: Connection) -> Session:  # noqa: D102
        return Session(bind=connection)

    @injector.provider
    def session_factory(self) -> sessionmaker:  # noqa: D102
        return sessionmaker(bind=self._engine)

    @injector.provider
    def engine(self) -> Engine:
        return self._engine


class ElasticSearchMod(injector.Module):  # noqa: D101
    def __init__(self, es_url: str) -> None:  # noqa: D107
        self._url = es_url

    @injector.provider
    @injector.singleton
    def es(self) -> elasticsearch.Elasticsearch:  # noqa: D102
        logger.info("Creating ES client url=%s", self._url)
        return elasticsearch.Elasticsearch(self._url)


def install_auth_service(  # noqa: ANN201, D103
    container: injector.Injector, settings: Dict[str, str]
):
    container.binder.install(AuthInfrastructure())
    container.binder.install(
        JwtAuthInfrastructure(Path(settings["auth.jwt.pubkey.path"]))
    )


def request_configuration(conn: Connection, session: Session):  # noqa: ANN201, D103
    def configure_request_container(binder):  # noqa: ANN202
        binder.bind(Connection, to=injector.InstanceProvider(conn))
        binder.bind(Session, to=injector.InstanceProvider(session))

    return configure_request_container


def load_modules(group_name: str, app=None):  # noqa: ANN201, D103
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
