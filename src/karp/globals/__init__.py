from contextlib import contextmanager
from contextvars import ContextVar

from opensearchpy import OpenSearch
from sqlalchemy import pool
from sqlalchemy.engine import URL, Engine, create_engine
from sqlalchemy.orm import Session

from karp.main.config import DATABASE_URL, env

__all__ = ["es", "session"]


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


# engine and os_client are created once per FastAPI instance / CLI invocation
# SQLAlchemy engine
_engine_ctx_var: ContextVar[Engine] = ContextVar("engine")
# OpenSearch client
os_client: Proxy[OpenSearch] = Proxy(ContextVar("os_client"))

# session is created for each request / CLI invocation
session: Proxy[Session] = Proxy(ContextVar("session"))


def create_db_engine():
    _engine_ctx_var.set(_create_db_engine(DATABASE_URL))


def create_es():
    os_client_instance = OpenSearch(env("OPENSEARCH_HOST"), request_timeout=300)
    os_client.ctx_var.set(os_client_instance)


@contextmanager
def new_session():
    """
    Creates a db session.
    """

    session_obj = Session(bind=_engine_ctx_var.get(), close_resets_only=False)
    session_token = session.set(session_obj)

    # use session.begin()??
    try:
        yield
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        session.reset(session_token)


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
