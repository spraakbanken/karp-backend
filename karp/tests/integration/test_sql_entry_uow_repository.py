from karp.lex_infrastructure.repositories import SqlEntryUowRepository


def test_create_sql_entry_uow_repo(sqlite_session_factory):
    session = sqlite_session_factory()

    repo = SqlEntryUowRepository(entry_uow_factory=None, session=session)
