from sqlalchemy.engine import Connection  # noqa: D100


class SqlQuery:  # noqa: D101
    def __init__(self, conn: Connection):  # noqa: D107, ANN204
        self._conn = conn
