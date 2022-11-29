import pytest

from karp.lex_infrastructure.repositories.sql_entries import SqlEntryRepository

from karp.tests.unit.lex import factories
from karp.utility.time import utc_now


@pytest.fixture(name="entry_repo")
def fixture_entry_repo(sqlite_session_factory):
    session = sqlite_session_factory()
    entry_repo = SqlEntryRepository.from_dict(
        name="test_name",
        resource_config={},
        session=session,
    )
    yield entry_repo

    entry_repo.teardown()


@pytest.fixture(name="entry_repo2")
def fixture_entry_repo2(sqlite_session_factory):
    session = sqlite_session_factory()
    entry_repo = SqlEntryRepository.from_dict(
        name="test_name2",
        resource_config={},
        session=session,
    )
    yield entry_repo

    entry_repo.teardown()


def test_create_entry_repository(entry_repo):
    assert entry_repo.entity_ids() == []


def test_save_entry_to_entry_repo(entry_repo):
    entry = factories.EntryFactory()
    entry_repo.save(entry)

    assert entry_repo.by_id(entry.id).version == entry.version


def test_update_entry_to_entry_repo(entry_repo):
    entry = factories.EntryFactory()
    entry_repo.save(entry)

    entry.update_body({"body": "changed"}, user="kristoff@example.com", message="hi")
    entry_repo.save(entry)

    assert entry_repo.by_id(entry.id).version == entry.version
    assert entry_repo.by_id(entry.id, version=1).version == 1


def test_discard_entry_and_insert_new(entry_repo):
    entry = factories.EntryFactory(last_modified=utc_now() - 3600.0, body={"a": "b"})
    entry_repo.save(entry)

    entry.discard(
        user="kristoff@example.com",
        message="hi",
    )
    assert entry.discarded
    entry_repo.save(entry)

    assert entry_repo.entity_ids() == []

    entry2 = factories.EntryFactory(body={"a": "b"})
    entry_repo.save(entry2)

    assert entry_repo.entity_ids() == [entry2.entity_id]


def test_create_entry_repository2(entry_repo2):
    assert entry_repo2.entity_ids() == []


class TestSqlEntryRepoGetHistory:
    def test_discard_entry_and_insert_new(self, entry_repo):
        pass
