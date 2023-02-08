from sqlalchemy.engine import Connection


class SqlQuery:
    def __init__(self, conn: Connection):
        self._conn = conn
