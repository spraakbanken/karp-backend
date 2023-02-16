from sqlalchemy import create_engine, orm, pool


class Database:  # noqa: D101
    def __init__(self, db_url: str) -> None:  # noqa: D107
        kwargs = {}
        if str(db_url).startswith("sqlite"):
            kwargs["poolclass"] = pool.SingletonThreadPool
            kwargs["connect_args"] = {"check_same_thread": False}
        self._engine = create_engine(db_url, echo=True, future=True, **kwargs)
        self.session_factory = orm.sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self._engine,
        )

    def disconnect(self):  # noqa: ANN201, D102
        pass


#    @contextmanager
#    def session(self) -> Callable[..., AbstractContextManager[Session]]:
#        session: Session = self._session_factory()
#        try:
#            yield session
#        except Exception:
#            logger.exception('Session rollback because of exception')
#            session.rollback()
#            raise
#        finally:
#            session.close()
