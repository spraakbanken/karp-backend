from sqlalchemy.orm import Session  # noqa: D100


class SqlQuery:  # noqa: D101
    def __init__(self, session: Session):  # noqa: D107, ANN204
        self._session = session
