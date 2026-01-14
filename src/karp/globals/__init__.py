from contextlib import contextmanager
from contextvars import ContextVar

from elasticsearch import Elasticsearch
from sqlalchemy import pool
from sqlalchemy.engine import URL, Engine, create_engine
from sqlalchemy.orm import Session

from karp.main.config import DATABASE_URL, env

__all__ = ["es", "es_search_service", "session"]


class Proxy[T]:
    def __init__(self, ctx_var: ContextVar[T]):
        self.ctx_var = ctx_var

    @property
    def _obj(self) -> T:
        try:
            return self.ctx_var.get()
        except LookupError as e:
            raise RuntimeError(f"No value set in ContextVar for this context") from e

    def set(self, obj):
        return self.ctx_var.set(obj)

    def reset(self, token):
        self.ctx_var.reset(token)

    def __getattr__(self, name):
        return getattr(self._obj, name)


# engine and es are created once per FastAPI worker / CLI invocation
_engine_ctx_var: ContextVar[Engine] = ContextVar("engine")
es: Proxy[Elasticsearch] = Proxy(ContextVar("es"))

# session and es_search_service are recreated for each request / CLI invocation
es_search_service: Proxy = Proxy(ContextVar("es_search_service"))  # TODO typing, circular dep. issue
session: Proxy[Session] = Proxy(ContextVar("session"))


def create_db_engine():
    _engine_ctx_var.set(_create_db_engine(DATABASE_URL))


def create_es():
    es_obj = Elasticsearch(env("ELASTICSEARCH_HOST"), request_timeout=300)
    es.ctx_var.set(es_obj)


@contextmanager
def new_session():
    """
    Creates a db session and an instance of EsSearchService.

    # TODO refactor: ESSearchService and the classes used in it does not need to be classes and can be modules. Restart is required after schema changes etc.
    """

    session_obj = Session(bind=_engine_ctx_var.get(), close_resets_only=False)
    session_token = session.set(session_obj)

    from karp.search.infrastructure.es.search_service import EsSearchService

    es_token = es_search_service.set(EsSearchService())

    # use session.begin()??
    try:
        yield
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        session.reset(session_token)
        es_search_service.reset(es_token)


def _create_db_engine(db_url: URL) -> Engine:
    kwargs = {}
    if str(db_url).startswith("sqlite"):
        kwargs["poolclass"] = pool.SingletonThreadPool
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        # 28800 s is the default value for MariaDB to drop connections, causing errors unless "pool_recycle" is set
        kwargs["pool_recycle"] = env.int("MARIADB_IDLE_TIMEOUT", 28800)
        kwargs["max_overflow"] = -1
    engine_echo = False
    return create_engine(db_url, echo=engine_echo, future=True, **kwargs)
