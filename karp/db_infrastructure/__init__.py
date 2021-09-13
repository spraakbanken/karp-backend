from sqlalchemy import create_engine, orm


class Database:
    def __init__(self, db_url: str) -> None:
        self._engine = create_engine(db_url, echo=True)
        self.session_factory = orm.sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self._engine,
        )

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
