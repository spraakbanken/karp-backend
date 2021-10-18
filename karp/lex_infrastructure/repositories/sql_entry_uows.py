from sqlalchemy import orm as sa_orm


class SqlEntryUowRepository:
    def __init__(self, session: sa_orm.Session) -> None:
        self._session = session
