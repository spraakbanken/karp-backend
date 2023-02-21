from karp.lex_infrastructure.repositories import SqlEntryUowRepository


def test_create_sql_entry_uow_repo(sqlite_session_factory):  # noqa: ANN201
    session = sqlite_session_factory()

    repo = SqlEntryUowRepository(entry_uow_factory=None, session=session)  # noqa: F841
