import logging  # noqa: D100, I001
from pathlib import Path
import threading
from typing import Dict, Type
import sys

from karp.entry_commands import EntryCommands
from karp.lex.application.repositories import ResourceRepository
from karp.lex_infrastructure import ResourceQueries, EntryQueries
from karp.resource_commands import ResourceCommands
from karp.search_commands import SearchCommands
from karp.search_infrastructure.repositories.es6_indicies import Es6Index

try:
    from importlib.metadata import entry_points
except ImportError:
    # used if python == 3.9
    from importlib_metadata import entry_points  # type: ignore

import elasticsearch  # noqa: I001
import injector
from injector import Provider, T
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import Session

from karp.auth_infrastructure import (
    AuthInfrastructure,
    JwtAuthInfrastructure,
)

from contextlib import contextmanager

logger = logging.getLogger(__name__)


class CommandsMod(injector.Module):  # noqa: D101
    @injector.provider
    def entry_commands(
        self,
        session: Session,
        resources: ResourceRepository,
        index: Es6Index,
    ) -> EntryCommands:
        return EntryCommands(
            session=session,
            resources=resources,
            index=index,
        )

    @injector.provider
    def resource_commands(
        self, session: Session, resources: ResourceRepository, index: Es6Index
    ) -> ResourceCommands:
        return ResourceCommands(session=session, resources=resources, index=index)

    @injector.provider
    def search_commands(
        self,
        index: Es6Index,
        resource_queries: ResourceQueries,
        entry_queries: EntryQueries,
    ) -> SearchCommands:
        return SearchCommands(
            index=index, resource_queries=resource_queries, entry_queries=entry_queries
        )


class Db(injector.Module):  # noqa: D101
    def __init__(self, engine: Engine) -> None:  # noqa: D107
        self._engine = engine

    @injector.provider
    @injector.singleton
    def engine(self) -> Engine:
        return self._engine

    # No session is set up by default, since the lifetime of the session (i.e.
    # who should close it) would be unclear. Instead, with_new_session or
    # new_session can be used to create a fresh session.


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
    container.binder.install(JwtAuthInfrastructure(Path(settings["auth.jwt.pubkey.path"])))


def with_new_session(container: injector.Injector):  # noqa: ANN201, D103
    session = Session(bind=container.get(Engine), close_resets_only=True)
    # Note on close_resets_only=False: this will detect cases where we call close()
    # while another piece of code is still using the session. If you plan to remove this,
    # be careful about the cache in SqlResourceRepository.

    def configure_child(binder):  # noqa: ANN202
        binder.bind(Session, to=injector.InstanceProvider(session))

    return container.create_child_injector(configure_child)


@contextmanager
def new_session(container: injector.Injector):
    container = with_new_session(container)
    with container.get(Session) as session:
        yield container


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
